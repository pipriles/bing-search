#!/usr/bin/env python3
# We have to check those with error
# So we can check if that's another site that has a shop
# Under the same domain

import requests as rq
import json
import re
import pandas as pd

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = { 
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36', 
    'accept-language': 'en' 
}
TIMEOUT = 5

def search_key(url, key):

    product_urls = []
    kwargs = { 'headers': HEADERS, 'timeout': TIMEOUT }
    params = {'q':'"'+key+'"'}

    res = rq.get(url, params=params, **kwargs)
    res.raise_for_status() # Raise exception if there was an error

    # List comprehension FTW
    soup = BeautifulSoup(res.text,"html.parser")
    anchor = soup.select("a")
    hrefs = list(map(lambda x: x.get('href'),anchor))
    hrefs = list(set(hrefs))
    hrefs = list(filter(lambda x: x != None,hrefs))
    products = list((filter(lambda x: re.match(r'\/products\/',x),hrefs)))

    # Put heuristic here
    for product in products:
        product_urls.append(urljoin(url, product))

    return product_urls

def scrape_products(product_urls, key):

    data = []
    kwargs = { 'headers': HEADERS, 'timeout': TIMEOUT }
    mregex = re.compile( 
        r'var meta = {"product":{"id":[^,]*,"vendor":"([^"]*)","type":"([^"]*)',
        flags=re.I )

    for ur in product_urls:
        res = rq.get(ur, **kwargs)

        if res.status_code != 200: 
            continue

        html = res.text

        # Match keyword inside html
        pattern = r'(?:^|[^a-zA-Z]){}(?:$|[^a-zA-Z])'.format(key)
        match = re.search(pattern, html, flags=re.I)
        if match is None: continue

        # Extract data from meta
        meta = mregex.search(html)
        if meta is None: continue

        data.append({ 'url': ur, 'vendor': meta.group(1), 
                'type': meta.group(2), 'key': key })
        break

    return data

def load_url(filename):
    urls = []
    with open(filename, 'r', encoding='utf-8') as f:    
        urls = f.readlines()
    if urls:
    	htt = 'http://'    
        # Bello el comentario
    	urls = [htt + x.replace('\u2028','').strip() + "/search" for x in urls] #quiza cambiarlo
    return urls

def write_json(data):
    with open("pages.json","w") as f:
        json.dump(data, f, indent=4)

def scrape(keywords, urls):
    total = []
    for url in urls:
        print(url)
        for key in keywords:
            print(key)
            # Beautiful
            try:
                product_urls = search_key(url,key)
            except rq.exceptions.HTTPError as e:
                print('Error in url:', e)
                break
            try:
                # They said that with 2 is enough
                print(product_urls)
                total += scrape_products(product_urls[:2], key)
            except Exception as e:
                print(e)
        write_json(total)
    return total

############################################

# Safe add scheme to website
def add_scheme(url, scheme='http'):

    if not url \
    or re.match(r'[^\:\/]+\:\/\/', url):
        return url

    url = re.sub(r'^\:?\/*', '//', url)
    parsed = urlparse(url, scheme=scheme)
    return parsed.geturl()

def prepare_url(website):
    url = add_scheme(website)
    return urljoin(url, '/search') if url else None

def quiet_exit(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            return
    return wrapper

class ShopifySpider:

    """ Search for keywords inside a shop """

    def __init__(self, keywords):
        self.keywords = keywords 
        self.result = []

    def scrape_websites(self, websites):

        index = 1
        for url in websites:
            # Search keyword inside search
            print('Processing %s, %s' % (index, url))
            self.search_keywords(url)
            index += 1

    def search_keywords(self, url):

        for k in self.keywords:

            products = []
            print('- %s:' % k, end=' ')

            try:
                products = search_key(url, k)
                print(len(products))

            except rq.exceptions.HTTPError as e:
                print('%s...' % str(e)[:16])
                break

            except Exception as e:
                print('%s...' % str(e)[:73])
                continue

            # Max 2 first products
            self.scrape_products(products, k, 2)

        # Report how much was scraped so far
        print('%s found\n' % len(self.result))

    def scrape_products(self, products, k, limit=None):

        # Scrape each product url and 
        # search for the keyword
        try:
            result = scrape_products(products[:limit], k)
            self.result += result
            if result:
                found = result[0]
                print('  Found! %s' % found.get('url'))
        except Exception as e:
            print('%s...' % str(e)[:73])

    def dump_json(self, filename):
        with open(filename, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=4)

    # Not yet implemented
    def dump_csv(self, filename):
        df = pd.DataFrame(self.result)
        df.to_csv(filename, index=None)

@quiet_exit
def main():
    keywords = ["teelaunch", "pillow profits", "printify", "printful", 
        "gotten", "customcat", "custom cat", "viralstyle", 
        "gooten", "kite", "scalable press", "gearlaunch", "isikel" ]

    filename = './bruno.csv'
    df = pd.read_csv(filename, index_col=False)
    websites = df.iloc[:,1] # Shop domain
    websites = websites[websites != 'REDACTED']
    websites = websites.drop_duplicates()
    websites = websites.apply(prepare_url)

    # Test if website is not down
    # Then try to crawl it

    try:
        spider = ShopifySpider(keywords)
        spider.scrape_websites(websites)
    finally:
        spider.dump_json('pages.json')
        spider.dump_csv('pages.csv')

    # data = scrape(keywords, websites)
    # write_json(data)

############################################

# def main():
#     try:
#         keywords = ["teelaunch", "pillow profits", "printify", "printful", 
#             "gotten", "customcat", "custom cat", "viralstyle", 
#             "gooten", "kite", "scalable press", "gearlaunch", "isikel"]
# 
#         urls = load_url("bruno.in") # Fucking pandas
#         total = scrape(keywords, urls)
#         write_json(total)
#     except KeyboardInterrupt:
#         pass

if __name__ == '__main__':
    main()
