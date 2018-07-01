#!/usr/bin/env python3

import bing
import re
import random
import pandas as pd
import sys

def _keywords_query(site, keywords=[]):

    query = 'site:{}'.format(site)
    keywords = list(keywords)

    if keywords:
        random.shuffle(keywords)
        k_query = [ '"{}"'.format(k) for k in keywords ]
        k_query = ' OR '.join(k_query)
        k_query = ' ({}) '.format(k_query)
        query += k_query

    return query

def keywords_search(site, keywords=[]):

    query = _keywords_query(site, keywords)

    result = { k: '' for k in keywords }
    result['_count'] = 0
    result['Domain'] = site

    for r in bing.search(query):
        for k in keywords:
            snippet = r.get('snippet', '')
            if not result[k] and \
                re.search(k, snippet, re.I):
                result[k] = r.get('url')
        result['_count'] += 1

    return result

def prepare_input(filename, keywords=[]):

    df1 = pd.read_csv(filename, dtype=str)
    df1 = df1.iloc[:, 0] # Assume first column has the sites
    df2 = pd.DataFrame(index=df1.index, columns=keywords)

    return pd.concat([df1, df2], axis=1)

def search_websites(filename):

    keywords = [ "teelaunch", "pillow profits", 
        "printify", "printful", "customcat"]

    websites = prepare_input(filename, keywords)
    length = len(websites)
    results = []

    try:
        for index, row in websites.iterrows():
            print('{:.0f}%'.format(100*index/length), end=' ')
            print('-', row[0])

            # Work just first column
            kcolumns = row[1:].notna()
            if kcolumns.any(): continue

            site = row[0]
            result = keywords_search(site, keywords)
            results.append(result)

    finally:
        # Write that shit
        columns = [ 'Domain', *keywords, '_count' ]
        df = pd.DataFrame(results)
        df[columns].to_csv('results.csv', index=None)

def main():

    if len(sys.argv) != 2:
        print('Usage: ./keywords.py [FILENAME]')
        return

    try:
        filename = sys.argv[1]
        search_websites(filename)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()

