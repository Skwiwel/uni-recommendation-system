package service

import (
	"log"
	"net/http"
	"os"
	"time"
)

func Run(abTestOn bool) {
	errChan := make(chan error, 10)

	recommendationService, err := makeRecommendationService(abTestOn)
	if err != nil {
		log.Println("Could not create a recommendation service: " + err.Error())
		os.Exit(1)
	}

	go runRecommendationGenInIntervals(5*time.Minute, recommendationService)

	serviceMux := http.NewServeMux()
	serviceMux.HandleFunc("/recommendations", recommendationService.HttpHandler)
	serviceServer := &http.Server{Addr: ":80", Handler: serviceMux}

	go func() {
		errChan <- serviceServer.ListenAndServe()
	}()

	log.Println("Service operational")

	for {
		select {
		case err := <-errChan:
			if err != nil && err.Error() != "http: Server closed" {
				log.Println(err)
			}
		}
	}
}

func runRecommendationGenInIntervals(interval time.Duration, s RecommendationService) {
	s.GenRecommendations()
	for range time.Tick(interval) {
		s.GenRecommendations()
	}
}
