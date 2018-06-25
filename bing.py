#!/usr/bin/env python3

import requests as rq
import itertools
import re
import pandas as pd

from bs4 import BeautifulSoup

BING_URL = 'https://www.bing.com/search'
HEADERS = { 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36', 'accept-language': 'en' }

def scrape_results(params):

    resp = rq.get(BING_URL, params=params, headers=HEADERS)
    if resp.status_code != 200:
        return None

    html = resp.text
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.select('#b_results li.b_algo a')
    snippets = soup.select('#b_results li.b_algo p')

    for a, p in zip(anchors, snippets):
        yield { 'url': a['href'], 'name': a.get_text(),
            'snippet': p.get_text() }

# Just a black box don't mess with it
def search(query, limit=10):

    params = { 'q': query }
    first = 1
    N = 10

    while True:

        reach = min(N, limit - first + 1)
        count = 0

        results = scrape_results(params)
        for r in itertools.islice(results, reach):
            yield r
            count += 1

        first += count
        params['first'] = first

        if count < reach or first > limit:
            break

def _search_keywords(domain, keywords=[]):

    query = 'site:{}'.format(domain)

    if keywords:
        k_query = ' OR '.join([ '"{}"'.format(k) for k in keywords ])
        k_query = ' ({})'.format(k_query)
        query += k_query

    print(query)

    cont = 0
    result = { k: '' for k in keywords }

    for r in search(query):
        for k in keywords:
            if re.search(k, r['snippet'], re.I):
                result[k] = r['url']
        cont += 1

    return result, cont

def search_websites(filename):

    # Keywords for Gabriela Youtube Problem
    keywords = ['buy', 'merch', 'sale', 'shop', 'store']
    data = pd.read_csv(filename)
    data.columns = ['websites']

    response = [ _search_keywords(w, keywords) for w in data.websites ]
    websites, counts  = tuple(zip(*response))

    frame1 = pd.DataFrame(list(websites), index=data.websites)
    frame2 = pd.DataFrame(list(counts), columns=['Count'])

    result = pd.concat([frame1, frame2], axis=1)
    return result

def search_keywords(domain, keywords=[]):

    query = 'site:{}'.format(domain)

    if keywords:
        k_query = ' OR '.join([ '"{}"'.format(k) for k in keywords ])
        k_query = ' ({})'.format(k_query)
        query += k_query

    print(query)

    cont = 0
    for r in search(query):
        print(r['url'], cont)
        cont += 1

    return cont

def main():
    pass

    
if __name__ == '__main__':
    main()

