package service

import (
	"database/sql"
	"errors"
	"fmt"
	"sync"

	_ "github.com/mattn/go-sqlite3"
)

type abTestHandler struct {
	dbConnection *sql.DB
	mu           sync.Mutex
}

type AbTestHandler interface {
	Close()
	AssignModelToUser(int) (RecommendationModel, error)
}

func makeAbTestHAndler() (AbTestHandler, error) {
	const dbFilepath = "../ab_testing/ab_test_db.db"
	var handler abTestHandler
	var err error
	handler.dbConnection, err = sql.Open("sqlite3", dbFilepath)
	if err != nil {
		return nil, &InternalError{"could not open db", err}
	}
	return &handler, nil
}

func (handler *abTestHandler) Close() {
	handler.dbConnection.Close()
}

func (handler *abTestHandler) AssignModelToUser(userID int) (RecommendationModel, error) {
	handler.mu.Lock()
	defer handler.mu.Unlock()

	row := handler.dbConnection.QueryRow("SELECT model_id FROM user_to_model WHERE user_id=" + fmt.Sprint(userID))
	var model RecommendationModel
	if err := row.Scan(&model); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			model, err = handler.findModelAndAssignToUser(userID)
			if err != nil {
				return 0, err
			}
		} else {
			return 0, &InternalError{"could not query db for user", err}
		}
	}
	return model, nil
}

func (handler *abTestHandler) findModelAndAssignToUser(userID int) (RecommendationModel, error) {
	usersInModel := make(map[RecommendationModel]int)
	rows, err := handler.dbConnection.Query("SELECT model_id, user_count FROM models")
	if err != nil {
		return 0, &InternalError{"could not query db for model user counts", err}
	}
	for rows.Next() {
		var model RecommendationModel
		var user_count int
		if err := rows.Scan(&model, &user_count); err != nil {
			return 0, &InternalError{"could not handle db anwer", err}
		}
		usersInModel[model] = user_count
	}
	rows.Close()

	var minModel RecommendationModel
	minUserCount := 0
	for model, userCount := range usersInModel {
		if userCount <= minUserCount {
			minUserCount = userCount
			minModel = model
		}
	}

	stmt, err := handler.dbConnection.Prepare("INSERT INTO user_to_model (user_id, model_id) VALUES(?, ?)")
	if err != nil {
		return 0, &InternalError{"could not prepare db transaction", err}
	}
	_, err = stmt.Exec(userID, minModel)
	if err != nil {
		return 0, &InternalError{"could not insert into db", err}
	}

	stmt, err = handler.dbConnection.Prepare("UPDATE models SET user_count = user_count + 1 WHERE model_id=?")
	if err != nil {
		return 0, &InternalError{"could not prepare db transaction", err}
	}
	_, err = stmt.Exec(minModel)
	if err != nil {
		return 0, &InternalError{"could not update user_count in models", err}
	}

	return minModel, nil
}
