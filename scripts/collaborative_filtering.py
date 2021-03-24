#!/usr/bin/env python

import os
import sys
import json
import pandas as pd
import adjacency_matrix as am
from surprise import Dataset, Reader, SVD
from collections import defaultdict

SAVE_PATH = 'recommendations/collaborative/'

def prepare_data() -> (Dataset, pd.DataFrame, pd.DataFrame):
    sessions_data, _ = am.load_sessions_products()
    view_matrix, buy_matrix = am.gen_adjacency_matrices(sessions_data)
    combined_matrix = view_matrix + buy_matrix * 9

    ratings = combined_matrix.stack().reorder_levels(('user_id', 'product_id')).to_frame('rating').reset_index()
    ratings = ratings.drop(ratings[ratings.rating == 0].index)

    reader = Reader(rating_scale=(0.0, 10.0))
    return (Dataset.load_from_df(ratings, reader), view_matrix, buy_matrix)

def train() -> (list, pd.DataFrame, pd.DataFrame):
    data, views, purchases = prepare_data()

    trainset = data.build_full_trainset()
    algo = SVD(n_epochs=10, lr_all=0.005, reg_all=0.4)
    algo.fit(trainset)

    testset = trainset.build_anti_testset()
    return (algo.test(testset), views, purchases)

def recommendations(predictions: list, views: pd.DataFrame, purchases: pd.DataFrame, n: int = 10) -> defaultdict:
    top_n = defaultdict(list)
    for uid, iid, _, est, _ in predictions:
        top_n[uid].append((iid, est))

    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n

def save_to_files(recommendations_per_user: int = 10):
    predictions, views, purchases = train()
    top_n = recommendations(predictions, views, purchases, recommendations_per_user)
    for uid in top_n.keys():
        data = {}
        items = [iid for iid, _ in top_n.get(uid)]

        viewed = views.loc[uid]
        viewed = viewed[viewed != False]

        purchased = purchases.loc[uid]
        purchased = purchased[purchased != False]

        items = items + viewed.index.to_list()[:recommendations_per_user - len(items)]
        items = items + purchased.index.to_list()[:recommendations_per_user - len(items)]
        
        data['recommendations'] = items
        if not os.path.isdir(SAVE_PATH): 
            os.makedirs(SAVE_PATH)
        with open(SAVE_PATH + str(uid) + '.json', 'w') as outfile:
            json.dump(data, outfile)

if __name__ == "__main__":
    n = 10
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    save_to_files(n)