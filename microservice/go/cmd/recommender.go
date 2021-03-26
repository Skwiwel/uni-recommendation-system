package main

import (
	"flag"
	"fmt"
	"os"
	"reflect"
	"strings"

	"github.com/skwiwel/uni-ium-recommender/microservice/go/internal/service"
)

var (
	mode           *string
	modeOptionsSet = map[string]struct{}{
		"popularity":    {},
		"collaborative": {},
		"abtest":        {},
	}
)

func init() {
	mode = flag.String("mode", "abtest",
		"run service in one of the modes:\n\tpopularity - model based on most popular categories\n\tcollaborative - collaborative filtering model\n\tabtest - A/B testing mode; requires ab_testing db\n",
	)
}

func main() {
	flag.Parse()
	if _, ok := modeOptionsSet[*mode]; !ok {
		fmt.Fprintf(os.Stderr, "error: invalid `mode` argument entered; possible values are "+formatArgumentOptions(modeOptionsSet))
		os.Exit(1)
	}

	service.Run(*mode)
}

func formatArgumentOptions(optionsMap map[string]struct{}) string {
	optionListReflectValues := reflect.ValueOf(optionsMap).MapKeys()
	var optionListStringValues []string
	for _, v := range optionListReflectValues {
		optionListStringValues = append(optionListStringValues, v.Interface().(string))
	}
	return "[" + strings.Join(optionListStringValues, ", ") + "]"
}
