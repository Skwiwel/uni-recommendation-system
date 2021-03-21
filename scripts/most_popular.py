import sys
import pandas as pd
import numpy as np
from adjacency_matrix import load_sessions_products, gen_adjacency_matrices

def init() -> (dict, dict, pd.DataFrame):
    sessions_data, products_data = load_sessions_products()
    views_data, _ = gen_adjacency_matrices(sessions_data)

    sessions_data = sessions_data[sessions_data['event_type'].str.contains('VIEW_PRODUCT')]
    sessions_data = sessions_data.drop(['session_id', 'timestamp', 'event_type'], 'columns').drop_duplicates()

    category_popularity = sessions_data.join(products_data.set_index('product_id'), on='product_id').drop('price', 'columns')
    item_popularity = category_popularity
    category_popularity = pd.pivot_table(category_popularity, index='category_path', columns='user_id', aggfunc=np.count_nonzero)

    # Most popular categories for each user
    most_popular_categories = {}
    for column in category_popularity.columns:
        most_popular_categories[column[1]] = category_popularity[column].dropna().sort_values(ascending=False).to_frame('popularity').dropna()

    item_popularity = pd.pivot_table(item_popularity, index='product_id', columns='category_path', aggfunc=np.count_nonzero)

    # Most popular items for each category
    most_popular_items = {}
    for column in item_popularity.columns:
        most_popular_items[column[1]] = item_popularity[column].dropna().sort_values(ascending=False).to_frame('popularity')

    return (most_popular_categories, most_popular_items, views_data)

def recommendations(categories: dict, items: dict, views: pd.DataFrame, uid: int, n: int = 10) -> list:
    result = []
    for category, _ in categories[uid].iterrows():
        for item, _ in items[category].iterrows():
            if views.loc[uid, item] == False:
                result.append(item)
                if len(result) == n:
                    return result
    return result

if __name__ == "__main__":
    categories, items, views = init()
    print(recommendations(categories, items, views, int(sys.argv[1]), int(sys.argv[2])))