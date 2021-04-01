#!/usr/bin/env python

import os
import datetime
import numpy as np
import pandas as pd

DATA_DIR_RAW = 'data_raw/'
DATA_DIR_TARGET = 'data/'
SESSIONS_FILENAME = 'sessions.jsonl'
PRODUCTS_FILENAME = 'products.jsonl'

def clean_data():
    sessions_data, products_data = read_sessions_products()
    clean_products_data(products_data, sessions_data)
    clean_sessions_data(sessions_data)
    
def read_sessions_products() -> (pd.DataFrame, pd.DataFrame):
    sessions = read_from_json(DATA_DIR_RAW+SESSIONS_FILENAME)
    products = read_from_json(DATA_DIR_RAW+PRODUCTS_FILENAME)
    return (sessions, products)

def read_from_json(filepath):
    return pd.read_json(filepath, convert_dates=False, lines=True)

def clean_products_data(products_data: pd.DataFrame, sessions_data: pd.DataFrame):
    data = drop_unused_products(products_data, sessions_data)
    data = data.drop(columns=['product_name'])
    # Fix prices < 0
    data['price'] = data['price'].apply(lambda x: -x if x < 0 else x)
    # Fix too high prices; Assumes no price is higher than a million pln
    data['price'] = data['price'].apply(lambda x: x / 1e6 if x > 1e6 else x)
    save_to_json(data, DATA_DIR_TARGET+PRODUCTS_FILENAME, DATA_DIR_TARGET)
    
def drop_unused_products(products_data: pd.DataFrame, sessions_data: pd.DataFrame) -> pd.DataFrame:
    used_products = sessions_data['product_id'].unique()
    products_data = products_data[products_data['product_id'].isin(used_products)]
    return products_data

def clean_sessions_data(data: pd.DataFrame):
    for index, row in data.iterrows():
        if pd.isna(row['user_id']):
            session_data = data.loc[(data['session_id'] == row['session_id']) & pd.notna(data['user_id'])]
            if session_data.size > 0:
                data.loc[index, 'user_id'] = session_data['user_id'].values[0]

    if is_error_correlated(data, 'user_id') == False:
        data.dropna(subset=['user_id'], inplace=True)
    if is_error_correlated(data, 'product_id') == False:
        data.dropna(subset=['product_id'], inplace=True)

    data.drop(columns=['offered_discount', 'purchase_id'], inplace=True)
    save_to_json(data, DATA_DIR_TARGET+SESSIONS_FILENAME, DATA_DIR_TARGET)

def save_to_json(df, filepath, create_dir=None):
    if create_dir is not None and not os.path.isdir(create_dir): 
        os.mkdir(create_dir)
    df.to_json(filepath, orient='records', date_format='iso', lines=True)

def is_error_correlated(data: pd.DataFrame, column: str) -> bool:
    column_ptr = column + '_ptr'
    data.insert(len(data.columns), column_ptr, 0)
    data.loc[data[column].isnull(), column_ptr] = 1

    max_correlation = 0
    for data_column in data.columns:
        if data_column != column and data_column != column_ptr:
            compare_with = data[data_column]
            if data_column == 'timestamp':
                compare_with = compare_with.transform(lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S").timestamp())
            elif data_column == 'event_type':
                compare_with = compare_with.transform(lambda x: ord(x[0]))
            max_correlation = max(max_correlation, abs(compare_with.corr(data[column_ptr])))

    data.drop(column_ptr, 'columns', inplace=True)    
    return max_correlation >= 0.1

if __name__ == "__main__":
    clean_data()