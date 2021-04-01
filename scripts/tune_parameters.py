#!/usr/bin/env python

import sys
from random import uniform
from model_test import test
from collaborative_filtering import prepare_data
from adjacency_matrix import load_sessions_products

def tune_parameters(cutoff: int, jobs: int):
    session_data, products_data = load_sessions_products()
    session_data = session_data.head(int(session_data.index.size / 2))
    params = []
    precision = 0
    recall = 0

    for i in range(cutoff):
        print(i, '/', cutoff, end='\r')
        params_test = [100, 20, uniform(0, 0.1), uniform(0, 1), uniform(0, 0.05), uniform(0, 0.2)]
        precision_test, recall_test = test('cf', 10, session_data, products_data, jobs, params_test, True)

        if (precision_test + recall_test > precision + recall):
            params = params_test
            precision = precision_test
            recall = recall_test

    print('\nBest precision@10 =', precision)
    print('Best recall@10 =', recall)
    print('Best params:\n\tn_factors =', params[0],'\n\tn_epochs =', params[1],'\n\tinit_mean =', params[2],
    '\n\tinit_std_dev =', params[3],'\n\tlr_all =', params[4], '\n\treg_all =', params[5])

if __name__ == "__main__":
    cutoff = 1000
    jobs = 8
    for i in range(1, len(sys.argv)):
        if sys.argv[i].startswith('-c'):
            cutoff = int(sys.argv[i][2:])
        elif sys.argv[i].startswith('-j'):
            jobs = int(sys.argv[i][2:])
    tune_parameters(cutoff, jobs)