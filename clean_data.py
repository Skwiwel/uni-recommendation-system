import numpy as np
import pandas as pd

DATA_DIR_RAW = 'data_raw/'
DATA_DIR_TARGET = 'data/'
SESSIONS_FILENAME = 'sessions.jsonl'
PRODUCTS_FILENAME = 'products.jsonl'

def clean_data():
    clean_products_data()
    clean_sessions_data()

def clean_products_data():
    data = read_from_json(DATA_DIR_RAW+PRODUCTS_FILENAME)
    data = data.drop(columns=['product_name'])
    # Fix prices < 0
    data['price'] = data['price'].apply(lambda x: -x if x < 0 else x)
    # Fix too high prices; Assumes no price is higher than a million pln
    data['price'] = data['price'].apply(lambda x: x / 1e6 if x > 1e6 else x)
    save_to_json(data, DATA_DIR_TARGET+PRODUCTS_FILENAME)

def clean_sessions_data():
    data = read_from_json(DATA_DIR_RAW+SESSIONS_FILENAME)
    data = data.drop(columns=['offered_discount', 'purchase_id'])
    for index, row in data.iterrows():
        if pd.isna(row['user_id']):
            session_data = data.loc[(data['session_id'] == row['session_id']) & pd.notna(data['user_id'])]
            if session_data.size > 0:
                data.loc[index, 'user_id'] = session_data['user_id'].values[0]
    data = data.dropna()
    save_to_json(data, DATA_DIR_TARGET+SESSIONS_FILENAME)

def read_from_json(filepath):
    return pd.read_json(filepath, convert_dates=False, lines=True)

def save_to_json(df, filepath):
    df.to_json(filepath, orient='records', date_format='iso', lines=True)

if __name__ == "__main__":
    clean_data()