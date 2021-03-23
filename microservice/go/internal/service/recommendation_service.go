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
	"strconv"
)

type RecommendationService interface {
	HttpHandler(http.ResponseWriter, *http.Request)
	GenRecommendations()
}

type recommendationService struct {
	recommendationDirs map[RecommendationModel]string
	modelScripts       map[RecommendationModel]string
	testHandler        AbTestHandler
}

type RecommendationModel int

const (
	Popularity    RecommendationModel = 1
	Collaborative RecommendationModel = 2
)

const recommendationsDirectory = "../recommendations/"

func makeRecommendationService() (RecommendationService, error) {
	var s recommendationService
	s.recommendationDirs = map[RecommendationModel]string{
		Popularity:    recommendationsDirectory + "popularity/",
		Collaborative: recommendationsDirectory + "collaborative/",
	}
	s.modelScripts = map[RecommendationModel]string{
		Popularity:    "",
		Collaborative: "",
	}

	testHandler, err := makeAbTestHAndler()
	if err != nil {
		return nil, err
	}
	s.testHandler = testHandler

	return &s, nil
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
	Recommendations []string `json:"recommendations"`
}

func makeRecommendationsResource(userID int, recommendations []string) *ResourceObject {
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

		model, err := s.testHandler.AssignModelToUser(userID)
		if err != nil {
			log.Println("Could not assign model to user: " + err.Error())
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		filename := s.recommendationDirs[model] + fmt.Sprint(userID) + ".json"
		recommendationsJsonFile, err := os.Open(filename)
		defer recommendationsJsonFile.Close()
		if err != nil {
			log.Println("Could not open file <" + filename + ">: " + err.Error())
			w.WriteHeader(http.StatusInternalServerError)
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
	// Hardcoded to search for a recommendation file in Popularity model
	filename := s.recommendationDirs[Popularity] + fmt.Sprint(userID) + ".json"
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		return false
	}
	return true
}

func (s *recommendationService) GenRecommendations() {
	log.Println("Generating recommendations")
}
