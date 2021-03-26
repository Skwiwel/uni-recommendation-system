#!/usr/bin/env python

import sys
import numpy as np
import pandas as pd

DATA_DIR = 'data/'
SESSIONS_FILENAME = 'sessions.jsonl'
PRODUCTS_FILENAME = 'products.jsonl'
USERS_FILENAME = 'users.jsonl'

def gen_adjacency_matrices(sessions_data: pd.DataFrame, boolean_matrices=True) -> (pd.DataFrame, pd.DataFrame):
    items_in_sessions = get_uniques(sessions_data, 'product_id')
    users_in_sessions = get_uniques(sessions_data, 'user_id')
    
    views_data = sessions_data[sessions_data['event_type'].str.contains('VIEW_PRODUCT')]
    buy_data = sessions_data[sessions_data['event_type'].str.contains('BUY_PRODUCT')]
   
    view_adjacency_matrix = pd.crosstab(views_data['user_id'], views_data['product_id'])
    buy_adjacency_matrix = pd.crosstab(buy_data['user_id'], buy_data['product_id'])

    for item in items_in_sessions:
        if item not in buy_adjacency_matrix:
            buy_adjacency_matrix.insert(len(buy_adjacency_matrix.columns), item, False)

    for user in users_in_sessions:
        if user not in buy_adjacency_matrix.index.to_list():
            buy_adjacency_matrix.loc[user,:] = False

    if boolean_matrices:
        view_adjacency_matrix = view_adjacency_matrix.astype(bool)
        buy_adjacency_matrix = buy_adjacency_matrix.astype(bool)

    return (view_adjacency_matrix, buy_adjacency_matrix)
    
def load_sessions_products() -> (pd.DataFrame, pd.DataFrame):
    sessions_data = pd.read_json(DATA_DIR+SESSIONS_FILENAME, lines=True)
    products_data = pd.read_json(DATA_DIR+PRODUCTS_FILENAME, lines=True)
    return (sessions_data, products_data)

def get_uniques(df, column_name) -> set:
    uniques = df[column_name].unique()
    uniques.sort()
    uniques = set(uniques)
    return uniques

if __name__ == "__main__":
    sessions_data, products_data = load_sessions_products()
    view_matrix, buy_matrix = gen_adjacency_matrices(sessions_data)
    print(view_matrix.astype(bool))
    print(buy_matrix.astype(bool))
