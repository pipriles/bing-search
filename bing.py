#!/usr/bin/env python3

import requests as rq
import itertools
import re
import json
import util

from bs4 import BeautifulSoup

BING_URL = 'https://www.bing.com/search'
HEADERS = { 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36', 'accept-language': 'en' }
MATCHES = []

def write_json(filename, data):
    if not data: return
    with open(filename, 'w', encoding='utf8') as f:
        json.dump(data, f, indent=4)

def load_url(filename):
    urls = []
    with open(filename, 'r', encoding='utf-8') as f:    
        urls = f.readlines()
    if urls:    
        urls = [x.replace('\u2028','').strip() for x in urls]
    return urls

@util.user_agent(HEADERS)
def search_keywords(domain, keywords=[]):
    query = 'site:{}'.format(domain)

    if keywords:
        k_query = ' OR '.join([ '"{}"'.format(k) for k in keywords ])
        k_query = ' ({})'.format(k_query)
        query += k_query

    cont = 0
    for r in search(query):
        text = r.get("snippet").lower()
        for keyword in keywords:
            if keyword in text:
                MATCHES.append(r)
        cont += 1

    return cont

def scrape_results(params):

    resp = rq.get(BING_URL, params=params, headers=HEADERS)
    if resp.status_code != 200:
        return None

    html = resp.text
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.select('#b_results li.b_algo a')
    snippets = soup.select('#b_results li.b_algo p')

    with open('log.html', 'w') as f:
        f.write(html)

    for a, p in zip(anchors, snippets):
       yield { 'url': a['href'], 'name': a.get_text(),'snippet': p.get_text() }

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

def scrape_sites(urls,keywords):
    for url in urls: 
        print(url)
        search_keywords(url,keywords)
    write_json("pages.json",MATCHES)

def main():
    keywords = ["teelaunch", "pillow profits", "printify", "printful", "customcat"]
    urls = load_url("domains.csv")
    scrape_sites(urls,keywords)

    
if __name__ == '__main__':
    main()

