package main

import (
	"flag"

	"github.com/skwiwel/uni-ium-recommender/microservice/go/internal/service"
)

var (
	abTestOn *bool
)

func init() {
	abTestOn = flag.Bool("abtest", false, "run service with A/B testing featrue")
}

func main() {
	flag.Parse()

	service.Run(*abTestOn)
}
