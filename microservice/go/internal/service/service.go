package service

import (
	"fmt"
	"log"
	"net/http"
)

func Run() {
	fmt.Println("Service goo")

	errChan := make(chan error, 10)

	popularityService := makePopularityService()

	serviceMux := http.NewServeMux()
	serviceMux.HandleFunc("/popularity", popularityService.HttpHandler)
	serviceMux.HandleFunc("/correlation", popularityService.HttpHandler)
	serviceServer := &http.Server{Addr: ":80", Handler: serviceMux}

	go func() {
		errChan <- serviceServer.ListenAndServe()
	}()

	fmt.Println("Service operational")

	for {
		select {
		case err := <-errChan:
			if err != nil && err.Error() != "http: Server closed" {
				log.Println(err)
			}
		}
	}
}

type RecommendationService interface {
	HttpHandler(http.ResponseWriter, *http.Request)
	GenRecommendations()
}

type popularityService struct {
}

func makePopularityService() RecommendationService {
	s := popularityService{}
	return &s
}

func (s *popularityService) HttpHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case "GET":
		fmt.Fprintf(w, "Recommendation")

	default:
		fmt.Fprintf(w, "Unrecognized")
	}
}

func (s *popularityService) GenRecommendations() {
	fmt.Println("Generating recommendations")
}
