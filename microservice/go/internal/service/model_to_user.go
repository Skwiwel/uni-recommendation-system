package service

type ModelToUserHandler interface {
	AssignModelToUser(int) (RecommendationModel, error)
}

type staticModelToUserHandler struct {
	model RecommendationModel
}

func makeStaticModelToUserHandler(model RecommendationModel) ModelToUserHandler {
	return &staticModelToUserHandler{model}
}

func (h *staticModelToUserHandler) AssignModelToUser(int) (RecommendationModel, error) {
	return h.model, nil
}
