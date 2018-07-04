#!/usr/bin/env python3

import pandas as pd
import glob

fulldir = glob.glob('./results/*')
csvs = [ x for x in fulldir if x.endswith('.csv') ]
dfs  = [ pd.read_csv(csv, dtype=str) for csv in csvs ]

result = pd.concat(dfs)
result.drop_duplicates(subset=['url', 'key'], inplace=True)

columns = ['URL', 'Vendor', 'Type', 'Key']
result.to_csv('TOTAL.csv', index=None, header=columns)

