package service

type abTestDB struct {
	usersPerModel map[RecommendationModel]int
	userToModel	map[string]RecommendationModel
}

func assignUserToModel(user_id string) (RecommendationModel, error) {
	const dbFilepath := "../ab_test/ab_test_db.json"
	recommendationsJsonFile, err := os.OpenFile(dbFilepath)
	defer recommendationsJsonFile.Close()
	if err != nil {
		w.WriteHeader(http.StatusForbidden)
		return
	}
}