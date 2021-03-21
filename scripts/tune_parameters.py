from surprise import SVD, Dataset
from surprise.model_selection import GridSearchCV
from collaborative_filtering import prepare_data

def tune_parameters():
    data = prepare_data()

    param_grid = {
        'n_epochs': [5, 10], 
        'lr_all': [0.002, 0.005],
        'reg_all': [0.4, 0.6]}
    gs = GridSearchCV(SVD, param_grid, measures=['rmse', 'mae'], cv=3)
    gs.fit(data)

    print(gs.best_score['rmse'])
    print(gs.best_params['rmse'])

if __name__ == "__main__":
    tune_parameters()