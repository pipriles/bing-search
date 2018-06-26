#!/usr/bin/env python3

import pandas as pd
import math
import bing
import re
import sys

# This function uses bing to search
# LinkedIn profiles.....
def search_profile(keywords):

    query  = ' '.join(keywords)
    query += ' Linkedin'

    in_regex = re.compile(r'\/in\/')
    for r in bing.search(query):
        if in_regex.search(r['url']): 
            return r

    return None

def replace_keys(d, old, new):
    result = {}
    for n, o in zip(new, old): 
        result[n] = d.pop(o)
    return result

def main():

    if len(sys.argv) != 2: 
        print('Usage: ./non_api.py FILENAME')
        return
    
    filename = sys.argv[1]
    data = pd.read_csv(filename, dtype=str)
    data.fillna('', inplace=True)
    results = []

    scraped = 0
    OLD_KEYS = [ 'name', 'url' ]
    NEW_KEYS = data.columns[3:5]
    TOTAL = len(data)

    try:
        for index, row in data.iterrows():
            print('{:.0f}%'.format(100*index/TOTAL), end=' ')
            keywords = row.iloc[:3]

            profile = row.iloc[4]
            if profile:
                non_empty = row.iloc[3:5]
                result = non_empty.to_dict()
                results.append(result)
                print(result.get('PROFILE'))
                continue

            profile = search_profile(keywords)
            if profile:
                scraped += 1
                result = replace_keys(profile, OLD_KEYS, NEW_KEYS)
                results.append(result)
                print(result.get('PROFILE'))
                continue

            print()
            results.append({})

    except KeyboardInterrupt:
        pass

    finally:
        print('Total scraped:', scraped)
        df1 = data.iloc[:,:3]
        df2 = pd.DataFrame(results)
        df = pd.concat([df1, df2], axis=1)
        df.to_csv('results.csv', index=None)
    
if __name__ == '__main__':
    main()
