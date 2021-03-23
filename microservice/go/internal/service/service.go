package service

import (
	"log"
	"net/http"
)

func Run() {
	errChan := make(chan error, 10)

	popularityService := makeRecommendationService()

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
