#!/usr/bin/env python

import os
import sys
import json
import pandas as pd
import adjacency_matrix as am
from surprise import Dataset, Reader, SVD
from collections import defaultdict

SAVE_PATH = 'recommendations/collaborative/'

def prepare_data(sessions_data: pd.DataFrame) -> (Dataset, pd.DataFrame, pd.DataFrame):
    view_matrix, buy_matrix = am.gen_adjacency_matrices(sessions_data)
    combined_matrix = view_matrix.astype(int) + buy_matrix.astype(int)

    ratings = combined_matrix.stack().reorder_levels(('user_id', 'product_id')).to_frame('rating').reset_index()
    ratings = ratings.drop(ratings[ratings.rating == 0].index)

    reader = Reader(rating_scale=(0.0, 2.0))
    return (Dataset.load_from_df(ratings, reader), view_matrix, buy_matrix)

def cf_train(sessions_data: pd.DataFrame) -> (list, pd.DataFrame, pd.DataFrame):
    data, views, purchases = prepare_data(sessions_data)

    trainset = data.build_full_trainset()
    algo = SVD(n_epochs=10, lr_all=0.005, reg_all=0.4)
    algo.fit(trainset)

    testset = trainset.build_anti_testset()
    return (algo.test(testset), views, purchases)

def cf_recommendations(predictions: list, views: pd.DataFrame, purchases: pd.DataFrame, user_id: int, n: int = 10) -> list:
    top_n = []
    for uid, iid, _, est, _ in predictions:
        if uid == user_id:
            top_n.append((iid, est))
    top_n.sort(key=lambda x: x[1], reverse=True)

    top_n = [iid for iid, _ in top_n]
    top_n = top_n[:n]

    viewed = views.loc[uid]
    viewed = viewed[viewed != False]

    purchased = purchases.loc[uid]
    purchased = purchased[purchased != False]

    top_n = top_n + viewed.index.to_list()[:n - len(top_n)]
    top_n = top_n + purchased.index.to_list()[:n - len(top_n)]

    return top_n

def save_to_files(recommendations_per_user: int = 10):
    sessions_data, _ = am.load_sessions_products()
    predictions, views, purchases = cf_train(sessions_data)

    if not os.path.isdir(SAVE_PATH): 
        os.makedirs(SAVE_PATH)

    for uid in views.index.to_list():
        data = {}
        data['recommendations'] = cf_recommendations(predictions, views, purchases, uid, recommendations_per_user)
        with open(SAVE_PATH + str(uid) + '.json', 'w') as outfile:
            json.dump(data, outfile)

if __name__ == "__main__":
    n = 10
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    save_to_files(n)