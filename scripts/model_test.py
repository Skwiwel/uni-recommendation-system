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
q: Queue, model: str, recommend: int, cf_params: list = []):
    train_session = session_data[(session_data['user_id'] != user) | (session_data['product_id'].isin(training_set[user]))]
    result = []

    if model == MODEL_MOST_POPULAR:
        categories, items, views_user, purchases_user = most_popular_init(train_session, products_data)
        result = most_popular_recommendations(categories, items, views_user, purchases_user, user, recommend)
    elif model == MODEL_COLLABORATIVE_FILTERING:
        predictions, views_user, purchases_user = cf_train(train_session, cf_params)
        result = cf_recommendations(predictions, views_user, purchases_user, user, recommend)
    elif model == MODEL_RANDOM:
        result = sample(views.columns.to_list(), recommend)

    relevant = 0
    for item in result:
        if purchases.loc[user, item] and item not in training_set[user]:
            relevant = relevant + 1

    # precision@k
    q.put(relevant / recommend)
    # recall@k
    q.put(relevant / max(1, purchases.loc[user].sum()))

def test(model: str, recommend: int, session_data: pd.DataFrame, products_data: pd.DataFrame, jobs: int, cf_params: list = [], quiet: bool = False) -> (float, float):
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
    users_list = list(training_set.keys())
    curr = 0

    processes = {}
    q = Queue()
    for i in range(0, users, jobs):
        for j in range(i, min(users, i + jobs)):
            user = users_list[j]
            processes[user] = Process(target=test_user, args=(session_data, products_data, training_set, views, purchases, user, q, model, recommend, cf_params,))
            processes[user].start()
        
        for j in range(i, min(users, i + jobs)):
            user = users_list[j]
            processes[user].join()
            precision = precision + q.get() / users
            recall = recall + q.get() / users
            curr = curr + 1

            if quiet == False:
                print('Progress:', curr, '/', users, end='\r')
    return precision, recall

if __name__ == '__main__':
    model = MODEL_COLLABORATIVE_FILTERING
    k = 10
    jobs = 8
    for i in range(1, len(sys.argv)):
        if sys.argv[i] in [MODEL_MOST_POPULAR, 'most_popular']:
            model = MODEL_MOST_POPULAR
        elif sys.argv[i] in [MODEL_COLLABORATIVE_FILTERING, 'collaborative_filtering']:
            model = MODEL_COLLABORATIVE_FILTERING
        elif sys.argv[i] in [MODEL_RANDOM, 'random']:
            model = MODEL_RANDOM
        if sys.argv[i].startswith('-j'):
            jobs = int(sys.argv[i][2:])
        elif sys.argv[i].startswith('-k'):
            k = int(sys.argv[i][2:])

    session_data, products_data = load_sessions_products()

    precision = 0.0
    recall = 0.0
    if model == MODEL_RANDOM:
        runs = 10
        for i in range(runs):
            precision_run, recall_run = test(model, k, session_data, products_data, jobs)
            precision = precision + precision_run / runs
            recall = recall + recall_run / runs
    else:
        precision, recall = test(model, k, session_data, products_data, jobs)
        
    print('\nPrecision@',k,':', precision, 'Recall@',k,':', recall)