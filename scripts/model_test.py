import sys
import pandas as pd
from multiprocessing import Process, Queue
from random import sample
from adjacency_matrix import load_sessions_products, gen_adjacency_matrices
from most_popular import most_popular_init, most_popular_recommendations
from collaborative_filtering import cf_train, cf_recommendations

MODEL_MOST_POPULAR = 'mp'
MODEL_COLLABORATIVE_FILTERING = 'cf'
MODEL_RANDOM = 'rand'

def test_user(session_data: pd.DataFrame, products_data: pd.DataFrame, training_set: dict, views: pd.DataFrame, purchases: pd.DataFrame, user: int,
q: Queue, model: str, recommend:int):
    train_session = session_data[(session_data['user_id'] != user) | (session_data['product_id'].isin(training_set[user]))]
    result = []

    if model == MODEL_MOST_POPULAR:
        categories, items, views_user, purchases_user = most_popular_init(train_session, products_data)
        result = most_popular_recommendations(categories, items, views_user, purchases_user, user, recommend)
    elif model == MODEL_COLLABORATIVE_FILTERING:
        predictions, views_user, purchases_user = cf_train(train_session)
        result = cf_recommendations(predictions, views_user, purchases_user, user, recommend)
    elif model == MODEL_RANDOM:
        result = sample(views.columns.to_list(), recommend)

    relevant = 0
    for item in result:
        if purchases.loc[user, item] and item not in training_set[user]:
            relevant = relevant + 1

    # precision@20
    q.put(relevant / recommend)
    # recall@20
    q.put(relevant / purchases.loc[user].sum())

def test(model: str, recommend: int) -> (float, float):
    session_data, products_data = load_sessions_products()
    views, purchases = gen_adjacency_matrices(session_data)

    training_set = {}
    for _, session in session_data.iterrows():
        user = session['user_id']
        product = session['product_id']
        if user not in training_set:
            training_set[user] = [product]
        elif len(training_set[user]) < 10:
            training_set[user].append(product)
    
    precision = 0.0
    recall = 0.0
    users = len(training_set.keys())
    curr = 0

    processes = {}
    q = Queue()
    for user in training_set.keys():
        processes[user] = Process(target=test_user, args=(session_data, products_data, training_set, views, purchases, user, q, model, recommend,))
        processes[user].start()
    
    for user in training_set.keys():
        processes[user].join()
        precision = precision + q.get() / users
        recall = recall + q.get() / users
        curr = curr + 1

        print('Progress:', curr, '/', users, end='\r')
    return precision, recall

if __name__ == '__main__':
    model = MODEL_COLLABORATIVE_FILTERING
    n = 20
    if len(sys.argv) > 1:
        if sys.argv[1] in [MODEL_MOST_POPULAR, 'most_popular']:
            model = MODEL_MOST_POPULAR
        elif sys.argv[1] in [MODEL_COLLABORATIVE_FILTERING, 'collaborative_filtering']:
            model = MODEL_COLLABORATIVE_FILTERING
        elif sys.argv[1] in [MODEL_RANDOM, 'random']:
            model = MODEL_RANDOM
        if len(sys.argv) > 2:
            n = int(sys.argv[2])

    precision = 0.0
    recall = 0.0
    if model == MODEL_RANDOM:
        runs = 10
        for i in range(runs):
            precision_run, recall_run = test(model, n)
            precision = precision + precision_run / runs
            recall = recall + recall_run / runs
    else:
        precision, recall = test(model, n)
        
    print('\nPrecision@',n,':', precision, 'Recall@',n,':', recall)