package service

import (
	"encoding/json"
	"errors"
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
	recommendationModel      string
	recommendationsDirectory string
}

const recommendationsDirectory = "../recommendations/"

func makePopularityService() RecommendationService {
	s := recommendationService{"popularity", recommendationsDirectory + "popularity/"}
	return &s
}
func makeCollaborativeService() RecommendationService {
	s := recommendationService{"collaborative", recommendationsDirectory + "collaborative/"}
	return &s
}

type RecommendationsFromFile struct {
	User_id         string
	Recommendations []string
}

type ResourceObject struct {
	Type       string      `json:"type"`
	Id         string      `json:"id"`
	Attributes interface{} `json:"attributes"`
}

type RecommendationsResourceAttributes struct {
	Recommendations []string `json:"recommendations"`
}

func makeRecommendationsResource(user_id string, recommendations []string) *ResourceObject {
	attributes := RecommendationsResourceAttributes{recommendations}
	r := ResourceObject{"user", user_id, attributes}
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

		filename := s.recommendationsDirectory + userID + ".json"
		recommendationsJsonFile, err := os.Open(filename)
		defer recommendationsJsonFile.Close()
		if err != nil {
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

func parseUserId(query url.Values, w http.ResponseWriter) (string, error) {
	userID := query.Get("user_id")
	if userID == "" {
		w.WriteHeader(http.StatusBadRequest)
		return "", errors.New("invalid used id")
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

func (s *recommendationService) GenRecommendations() {
	log.Println("Generating recommendations")
}
