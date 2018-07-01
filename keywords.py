#!/usr/bin/env python3
# [ ] 00
# [ ] 01
# [ ] 02
# [ ] 03
# [ ] 04
# [ ] 05
# [ ] 06
# [ ] 07
# [ ] 08
# [ ] 09

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

def search_websites(filename):

    keywords = [ "teelaunch", "pillow profits", 
        "printify", "printful", "customcat"]

    print('Processing input...')
    websites = prepare_input(filename, keywords)
    length = len(websites)
    results = []

    try:
        for index, row in websites.iterrows():
            print('{:.0f}%'.format(100*index/length), end=' ')

            # Work just first column
            kcolumns = row[1:-1].notna()
            if kcolumns.any(): 
                print('-', row[0], '!')
                results.append(row.to_dict())
                continue

            print('-', row[0])
            site = row[0]
            result = keywords_search(site, keywords)
            results.append(result)

    finally:
        # Write that shit
        columns = [ 'Domain', *keywords, '_count' ]
        offset = len(results)

        # Order columns
        df1 = pd.DataFrame(results, dtype=str)
        df1 = df1[columns]

        # Put not scraped sites
        df2 = websites.iloc[offset:,:]

        df = pd.concat([df1, df2])
        df.to_csv('results.csv', index=None)

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

