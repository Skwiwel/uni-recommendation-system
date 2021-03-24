#!/usr/bin/env python

import os
import sys
import json
import pandas as pd
import numpy as np
from adjacency_matrix import load_sessions_products, gen_adjacency_matrices

SAVE_PATH = 'recommendations/popularity/'

def get_similar_categories(categories: list) -> dict:
    parent_categories = {}
    for category in categories:
        parts = category.split(';')
        parts.pop()
        parent_categories[category] = parts
    
    similar_categories = {}
    for category in categories:
        similar_categories[category] = {}
        for other_category in categories:
            if category != other_category:
                commonality = category_commonality(parent_categories[category], parent_categories[other_category])
                if commonality in similar_categories[category]:
                    similar_categories[category][commonality].append(other_category)
                else:
                    similar_categories[category][commonality] = [other_category]
    
    return similar_categories

def category_commonality(a: list, b: list) -> int:
    i = 0
    j = 0
    while i < len(a) and j < len(b) and a[i] == b[j]:
        i = i + 1
        j = j + 1
    return i

def init() -> (dict, dict, pd.DataFrame, pd.DataFrame):
    sessions_data, products_data = load_sessions_products()
    views_data, purchases_data = gen_adjacency_matrices(sessions_data)

    sessions_data = sessions_data[sessions_data['event_type'].str.contains('VIEW_PRODUCT')]
    sessions_data = sessions_data.drop(['session_id', 'timestamp', 'event_type'], 'columns').drop_duplicates()

    category_popularity = sessions_data.join(products_data.set_index('product_id'), on='product_id').drop('price', 'columns')
    item_popularity = category_popularity
    category_popularity = pd.pivot_table(category_popularity, index='category_path', columns='user_id', aggfunc=np.count_nonzero)
    similar_categories = get_similar_categories(category_popularity.index.to_list())

    # Ordered categories for each user according to similarity to most popular category and popularity of itself
    sorted_categories = {}
    for column in category_popularity.columns:
        categories_by_views = category_popularity[column].sort_values(ascending=False).to_frame('popularity')
        most_popular_for_user = categories_by_views.iloc[0].name

        similar_categories_for_user = similar_categories[most_popular_for_user]
        ordered = categories_by_views.loc[most_popular_for_user].to_frame().transpose()

        i = len(most_popular_for_user.split(';')) - 1
        while i >= 0:
            if i in similar_categories_for_user:
                ordered = ordered.append(categories_by_views.loc[similar_categories_for_user[i]].sort_values('popularity', ascending=False))
            i = i - 1
        sorted_categories[column[1]] = ordered

    item_popularity = pd.pivot_table(item_popularity, index='product_id', columns='category_path', aggfunc=np.count_nonzero)

    # Most popular items for each category
    most_popular_items = {}
    for column in item_popularity.columns:
        most_popular_items[column[1]] = item_popularity[column].dropna().sort_values(ascending=False).to_frame('popularity')

    return (sorted_categories, most_popular_items, views_data, purchases_data)

def recommendations(categories: dict, items: dict, views: pd.DataFrame, purchases: pd.DataFrame, uid: int, n: int = 10) -> list:
    result = []
    viewed = []
    purchased = []

    for category, _ in categories[uid].iterrows():
        for item, _ in items[category].iterrows():
            if views.loc[uid, item] == False:
                result.append(item)
                if len(result) == n:
                    return result
            elif purchases.loc[uid, item] == False:
                viewed.append(item)
            else: 
                purchased.append(item)

    result = result + viewed[:n - len(result)]
    result = result + purchased[:n - len(result)]
    return result

def save_to_files(recommendation_per_user: int = 10):
    categories, items, views, purchases = init()
    for uid in categories.keys():
        data = {}
        data['recommendations'] = recommendations(categories, items, views, purchases, uid, recommendation_per_user)
        if not os.path.isdir(SAVE_PATH): 
            os.makedirs(SAVE_PATH)
        with open(SAVE_PATH + str(uid) + '.json', 'w') as outfile:
            json.dump(data, outfile)


if __name__ == "__main__":
    n = 10
    if len(sys.argv) > 1:
        n = sys.argv[1]
    save_to_files(int(n))