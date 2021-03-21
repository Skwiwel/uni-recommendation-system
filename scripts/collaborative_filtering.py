import sys
import pandas as pd
import adjacency_matrix as am
from surprise import Dataset, Reader, SVD
from collections import defaultdict

def prepare_data() -> Dataset:
    sessions_data, _ = am.load_sessions_products()
    view_matrix, buy_matrix = am.gen_adjacency_matrices(sessions_data)
    combined_matrix = view_matrix + buy_matrix * 9

    ratings = combined_matrix.stack().reorder_levels(('user_id', 'product_id')).to_frame('rating').reset_index()
    ratings = ratings.drop(ratings[ratings.rating == 0].index)

    reader = Reader(rating_scale=(0.0, 10.0))
    return Dataset.load_from_df(ratings, reader)

def train() -> list:
    data = prepare_data()

    trainset = data.build_full_trainset()
    algo = SVD(n_epochs=10, lr_all=0.005, reg_all=0.4)
    algo.fit(trainset)

    testset = trainset.build_anti_testset()
    return algo.test(testset)

def recommendations(predictions: list, n: int = 10) -> defaultdict:
    top_n = defaultdict(list)
    for uid, iid, _, est, _ in predictions:
        top_n[uid].append((iid, est))

    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n

if __name__ == "__main__":
    top_n = recommendations(train(), int(sys.argv[2]))
    user_ratings = top_n.get(int(sys.argv[1]))
    print([iid for (iid, _) in user_ratings])