package service

import (
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

func Run(mode string) {
	if err := checkModeAndPrintConfirmationMessage(mode); err != nil {
		fmt.Fprintf(os.Stderr, "error: unrecognized mode", err.Error())
		os.Exit(1)
	}

	recommendationService, err := makeRecommendationService(mode)
	if err != nil {
		log.Println("Could not create a recommendation service: " + err.Error())
		os.Exit(1)
	}

	go runRecommendationGenInIntervals(5*time.Minute, recommendationService)

	serviceMux := http.NewServeMux()
	serviceMux.HandleFunc("/recommendations", recommendationService.HttpHandler)
	serviceServer := &http.Server{Addr: ":80", Handler: serviceMux}

	errChan := make(chan error, 10)
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

func checkModeAndPrintConfirmationMessage(mode string) error {
	switch mode {
	case "popularity":
		fmt.Println("Running on popularity based model")
	case "collaborative":
		fmt.Println("Running on collaborative filtering based model")
	case "abtest":
		fmt.Println("Running in A/B test mode")
	default:
		return errors.New("invalid mode argument")
	}
	return nil
}

func runRecommendationGenInIntervals(interval time.Duration, s RecommendationService) {
	s.GenRecommendations()
	for range time.Tick(interval) {
		s.GenRecommendations()
	}
}
