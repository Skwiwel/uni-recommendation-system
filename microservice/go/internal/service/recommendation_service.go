package service

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"strconv"
)

type RecommendationService interface {
	HttpHandler(http.ResponseWriter, *http.Request)
	GenRecommendations()
}

type recommendationService struct {
	recommendationDirs map[RecommendationModel]string
	modelScripts       map[RecommendationModel][]string
	modelToUserHandler ModelToUserHandler
}

type RecommendationModel int

// These have to be aligned with the model_id's in the ab_test db
const (
	Popularity RecommendationModel = iota + 1
	Collaborative

	modelIndexLimit
)

var pythonCommand = "py"

const recommendationsDirectory = "recommendations/"
const scriptsDirectory = "scripts/"
const genNumRecommendations = "50"

func makeRecommendationService(abTestOn bool) (RecommendationService, error) {
	var err error
	pythonCommand, err = findPythonExecutable()
	if err != nil {
		return nil, err
	}

	var s recommendationService
	s.recommendationDirs = map[RecommendationModel]string{
		Popularity:    recommendationsDirectory + "popularity/",
		Collaborative: recommendationsDirectory + "collaborative/",
	}
	s.modelScripts = map[RecommendationModel][]string{
		Popularity:    {pythonCommand, scriptsDirectory + "collaborative_filtering.py", genNumRecommendations},
		Collaborative: {pythonCommand, scriptsDirectory + "most_popular.py", genNumRecommendations},
	}

	var modelToUserHandler ModelToUserHandler
	if abTestOn {
		modelToUserHandler, err = makeAbTestHAndler()
		if err != nil {
			return nil, err
		}
	} else {
		modelToUserHandler = makeStaticModelToUserHandler(Collaborative)
	}
	s.modelToUserHandler = modelToUserHandler

	return &s, nil
}

func findPythonExecutable() (string, error) {
	possiblePythonExeNames := []string{"py", "python3"}
	for _, candidateCommand := range possiblePythonExeNames {
		path, err := exec.LookPath(candidateCommand)
		if err == nil {
			return path, nil
		}
	}
	return "", errors.New("could not locate a python executable")
}

type RecommendationsFromFile struct {
	User_id         int
	Recommendations []string
}

type ResourceObject struct {
	Type       string      `json:"type"`
	Id         int         `json:"id"`
	Attributes interface{} `json:"attributes"`
}

type RecommendationsResourceAttributes struct {
	Recommendations []int `json:"recommendations"`
}

func makeRecommendationsResource(userID int, recommendations []int) *ResourceObject {
	attributes := RecommendationsResourceAttributes{recommendations}
	r := ResourceObject{"user", userID, attributes}
	return &r
}

func (s *recommendationService) HttpHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case "GET":
		q := r.URL.Query()
		userID, err := parseUserId(q, w)
		if err != nil {
			return
		}
		numRecommendations, err := parseNumRecommendations(q, w)
		if err != nil {
			return
		}

		userExists := s.checkUserExists(userID)
		if !userExists {
			w.WriteHeader(http.StatusForbidden)
			return
		}

		model, err := s.modelToUserHandler.AssignModelToUser(userID)
		if err != nil {
			log.Println("Could not assign model to user: " + err.Error())
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		filename := s.recommendationDirs[model] + fmt.Sprint(userID) + ".json"
		recommendationsJsonFile, err := os.Open(filename)
		defer recommendationsJsonFile.Close()
		if err != nil {
			// Somewhat normal due to the way users are checked for existance
			// No recommendation file from this model was generated for this user
			//log.Println("Could not open file <" + filename + ">: " + err.Error())
			w.WriteHeader(http.StatusForbidden)
			return
		}

		byteValue, _ := ioutil.ReadAll(recommendationsJsonFile)
		var recommendationAttributes RecommendationsResourceAttributes
		if err := json.Unmarshal(byteValue, &recommendationAttributes); err != nil {
			log.Println(err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		if numRecommendations > len(recommendationAttributes.Recommendations) {
			numRecommendations = len(recommendationAttributes.Recommendations)
		}
		recommendations := makeRecommendationsResource(userID, recommendationAttributes.Recommendations[:numRecommendations])

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(recommendations)

	default:
		w.WriteHeader(http.StatusBadRequest)
	}
}

func parseUserId(query url.Values, w http.ResponseWriter) (int, error) {
	userIdStr := query.Get("user_id")
	if userIdStr == "" {
		w.WriteHeader(http.StatusBadRequest)
		return 0, &RequestError{"invalid used id", errors.New("")}
	}
	userID, err := strconv.Atoi(userIdStr)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return 0, &RequestError{"invalid used id", errors.New("")}
	}
	return userID, nil
}

func parseNumRecommendations(query url.Values, w http.ResponseWriter) (int, error) {
	numRecommendations := 10
	numRecommendationsStr := query.Get("num")
	if numRecommendationsStr != "" {
		var err error
		numRecommendations, err = strconv.Atoi(numRecommendationsStr)
		if err != nil {
			log.Println(err)
			w.WriteHeader(http.StatusBadRequest)
			return 0, errors.New("invalid request")
		}
		if numRecommendations <= 0 {
			w.WriteHeader(http.StatusBadRequest)
			return 0, errors.New("invalid request")
		}
	}
	return numRecommendations, nil
}

func (s *recommendationService) checkUserExists(userID int) bool {
	for m := RecommendationModel(1); m < modelIndexLimit; m++ {
		filename := s.recommendationDirs[m] + fmt.Sprint(userID) + ".json"
		if _, err := os.Stat(filename); os.IsNotExist(err) {
			continue
		}
		return true
	}
	// No such file found
	return false
}

func (s *recommendationService) GenRecommendations() {
	log.Println("Cleaning data")
	var cleanDataCommand = []string{pythonCommand, scriptsDirectory + "clean_data.py"}
	c := exec.Command(cleanDataCommand[0], cleanDataCommand[1:]...)
	if err := c.Run(); err != nil {
		log.Println("Could not run data cleaning script: ", err)
		return
	}

	log.Println("Generating recommendations")
	for m := RecommendationModel(1); m < modelIndexLimit; m++ {
		script, ok := s.modelScripts[m]
		if !ok {
			log.Println("Could not acquire gen recommendation script for model <" + fmt.Sprint(m) + ">")
			continue
		}
		log.Println("Running script: ", script)
		c := exec.Command(script[0], script[1:]...)
		if err := c.Run(); err != nil {
			log.Println("Could not run gen recommendation script: ", err)
		}
	}

	log.Println("Finished generating recommendations")
}
