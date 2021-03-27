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

    i = 0
    correct_views = 0.0
    correct_purchases = 0.0
    while i < recommend and result[i] not in training_set[user]:
        if views.loc[user, result[i]]:
            correct_views = correct_views + 1
        if purchases.loc[user, result[i]]:
            correct_purchases = correct_purchases + 1
        i = i + 1

    q.put(correct_views / (1 + abs(i - recommend)) + 9.0 * correct_purchases / (1 + abs(i - recommend)))

def test(model: str, recommend: int) -> float:
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
    
    test_result = 0.0
    users = len(training_set.keys())
    curr = 0

    processes = {}
    q = Queue()
    for user in training_set.keys():
        processes[user] = Process(target=test_user, args=(session_data, products_data, training_set, views, purchases, user, q, model, recommend,))
        processes[user].start()
    
    for user in training_set.keys():
        processes[user].join()
        test_result = test_result + q.get()
        curr = curr + 1

        print('Progress: ', curr, ' / ', users, 'Result: ', test_result, end='\r')
    return test_result

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

    result = 0.0
    if model == MODEL_RANDOM:
        runs = 10
        for i in range(runs):
            result = result + test(model, n) / runs
    else:
        result = test(model, n)
        
    print('\n', result)