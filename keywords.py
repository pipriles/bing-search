#!/usr/bin/env python3
# [ ] 02 Missed
# [-] 19 Javier
# --------------
# Competitors
# Printify
# Printful
# Pillow Profits
# Gotten
# Custom Cat
# ViralStyle
# Gooten
# Kite
# Scalable Press
# GearLaunch
# Isikel
# --------------
# Shirt
# Mug
# Poster
# Blanket
# Pillow

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

    columns = [ 'Domain', *keywords, '_count' ]
    df = pd.read_csv(filename, dtype=str)
    
    df = [ df.get(k, pd.Series(index=df.index, name=k)) \
            for k in columns ]

    return pd.concat(df, axis=1)

def search_websites(filename, offset=0):

    keywords = [ "teelaunch", "pillow profits", 
        "printify", "printful", "customcat"]

    print('Processing input...')
    websites = prepare_input(filename, keywords)
    length = len(websites)
    results = []

    try:
        for index, row in websites.iloc[offset:].iterrows():
            print('{:.0f}%'.format(100*index/length), end=' ')
            print('-', index, row[0], end=' ')

            # Work just first column
            kcolumns = row[1:-1].notna()
            if kcolumns.any(): 
                print('!')
                results.append(row.to_dict())
                continue

            print()
            site = row[0]
            result = keywords_search(site, keywords)
            results.append(result)

    finally:
        # Write that shit
        columns = [ 'Domain', *keywords, '_count' ]
        amount = offset + len(results)

        # Begin from offset
        df0 = websites.iloc[:offset]

        # Order columns
        df1 = pd.DataFrame(results, dtype=str)
        df1 = df1[columns]

        # Put not scraped sites
        df2 = websites.iloc[amount:]

        df = pd.concat([df0, df1, df2])
        df.to_csv('results.csv', index=None)

def main():

    if len(sys.argv) < 2:
        print('Usage: ./keywords.py [FILENAME] [OFFSET]') 
        return

    params = dict(enumerate(sys.argv))

    try:
        filename = params.get(1)
        offset   = int(params.get(2, 0))
        search_websites(filename, offset)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()

