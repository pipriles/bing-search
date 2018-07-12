#!/usr/bin/env python3
# We have to check those with error
# So we can check if that's another site that has 
# a shop under the same domain
# Maybe we should change the timeout to 2 seconds

import requests as rq
import pandas as pd
import json
import re
import sys
import os
import glob

import functools
import multiprocessing as mp

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = { 
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36', 
    'accept-language': 'en' 
}
TIMEOUT = 3

def search_key(url, key):

    product_urls = []
    kwargs = { 'headers': HEADERS, 'timeout': TIMEOUT }
    params = { 'q': '"{}"'.format(key) }

    res = rq.get(url, params=params, **kwargs)
    res.raise_for_status() # Raise exception if there was an error

    html = res.text

    # List comprehension FTW
    # ----------------------
    # soup = BeautifulSoup(html,"html.parser")
    #
    # anchor = soup.find_all('a')
    # hrefs = [ x.get('href') for x in anchor ]
    # hrefs = list(dict.fromkeys(hrefs))
    # hrefs = [ x for x in hrefs if not x is None ]
    #
    # products = [ x for x in hrefs if re.match(r'\/products\/', x) ]
    # ----------------------

    # Wink wink (Heuristic)
    products = product_hrefs(html)

    for product in products:
        product_urls.append(urljoin(url, product))

    return product_urls

def search_products(product_urls, key):

    data = []
    kwargs = { 'headers': HEADERS, 'timeout': TIMEOUT }

    pattern  = r'var meta = {"product":{"id":[^,]*,"vendor"'
    pattern += r':"([^"]*)","type":"([^"]*)'
    mregex = re.compile(pattern, flags=re.I)

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
        break # Just one time

    return data

# --------------- Trump's Wall ---------------

def uncomment_soup(html):
    # Not satisfied with this solution
    uncommented = re.sub(r'(?:<!--)|(?:-->)', '', html)
    soup = BeautifulSoup(uncommented, 'html5lib') # Very slow
    return soup

def product_hrefs(html):

    pregex = re.compile(r'products\/')
    soup = uncomment_soup(html) # Should i do this?
    result = []

    # Heuristic to avoid extra calls
    imgs = soup.find_all('img')
    for img in imgs:
        parent = img.find_parent('a', href=pregex)
        if parent:
            href = parent.get('href')
            result.append(href)

    # Just in case there is no result
    if not result:
        anchors = soup.find_all('a', href=pregex)
        result = [ a.get('href') for a in anchors ]

    # Remove parameters and duplicates
    result = [ re.sub(r'(?:\#[^\?]*)?(?:\?.+)?$', '', x) for x in result ]
    result = list(dict.fromkeys(result)) # Remove duplicates, keep order
    return result

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

def hostname(url):
    url = add_scheme(url, 'http')
    parsed = urlparse(url)
    return parsed.hostname

def scrape_keywords(url, keywords=[]):

    found = []
    MAX_ = 2

    for k in keywords:
        products = []
        message = '- %s -> %s:' % (url, k)
        try:
            products = search_key(url, k)
            print(message, len(products))

            # Max 2 first products
            result = search_products(products[:MAX_], k)

        except rq.exceptions.HTTPError as e:
            code = e.response.status_code
            print(message, '%s...' % str(e)[:16])
            ret =  None, { 'url': url, 
                'code': code, 'message': str(e) }
            found.append(ret)
            break # Try with Javier candidates

        except Exception as e:
            print(message, '%s...' % str(e)[:73])
            ret = None, { 'url': url, 'message': str(e) }
            found.append(ret)
            continue

        # Shut up interrupt
        except KeyboardInterrupt: break

        if result:
            first = result[0]
            ret = first, None
            found.append(ret)
            print('  Found! %s' % first.get('url'))

    return found

def dump_json(filename, data):
    with open(filename, 'w', encoding='utf8') as fl:
        json.dump(data, fl, indent=2)
        print('JSON dumped')

def dump_csv(filename, data):
    if not data: return 
    columns = [ 'url', 'vendor', 'type', 'key' ]
    df = pd.DataFrame(data)
    df[columns].to_csv(filename, index=None)
    print('CSV Dumped')

def dump_log(filename, data):
    with open(filename, 'w', encoding='utf8') as fl: 
        json.dump(data, fl, indent=2)

def crawl_websites(domains, keys):

    scraped = []
    errors = []
    count = 0

    crawler = parallel_scrape(domains, keys)

    for result in crawler:

        for ret, err in result: 
            if ret: scraped.append(ret)
            if err: errors.append(err)

        # Report how much was scraped so far
        print('%s found\n' % len(scraped))
        count += 1

        yield { 'scraped': scraped,
            'errors': errors, 'count': count }

def parallel_scrape(domains, keys, N=12):

    with mp.Pool(N) as p:
        scraper = functools.partial(scrape_keywords, keywords=keys)
        yield from p.imap_unordered(scraper, domains)

def remove_found(filename, websites):

    try:
        df = pd.read_csv(filename)

        # Assume first column has the websites
        black = df.iloc[:,0] 
        print(len(black), 'Blacklisted...')

        # Get hostname and drop duplicates
        # This function is slow, improve
        black = black.apply(hostname)
        black = black.drop_duplicates()

        # Sadly ;(
        websites = websites.apply(hostname)

        # Match found in websites
        found = websites.isin(black)
        return websites[~found]

    except FileNotFoundError: 
        return websites

def parse_path(path):

    if os.path.isdir(path):
        path = os.path.join(path, '*.csv')

    files = glob.glob(path)
    files = [ x for x in files if os.path.isfile(x) ] 
    dfs   = [ pd.read_csv(csv, dtype=str) for csv in files ]
    return pd.concat(dfs)

def read_path(files, path='blacklist.in'):

    dfs = [ parse_path(p) for p in files ]
    df  = pd.concat(dfs)

    websites = df['Domain']
    websites = websites.drop_duplicates()

    # Remove blacklisted, it reads as csv
    websites = remove_found(path, websites)
    websites = websites.apply(prepare_url)
    return websites

def main():
    # keywords = ["teelaunch", "pillow profits", "printify", 
    #     "printful", "gotten", "customcat", "custom cat", 
    #     "viralstyle", "gooten", "kite", "scalable press", 
    #     "gearlaunch", "isikel" ]

    keywords = [ "shirt", "mug", "poster", "blanket", 
            "pillow", "gooten" ]

    if len(sys.argv) < 2:
        print('Usage: ./products.py [FILENAME]...')
        return

    files = sys.argv[1:]
    websites = read_path(files)

    try:
        name = os.path.basename(files[0])
        name = os.path.splitext(name)[0]

        progress = crawl_websites(websites, keywords)
        for stat in progress:

            scraped = stat.get('scraped')
            debug = { k: stat.get(k) for k in ('count', 'errors') }

            # Dump progress
            # dump_csv('%s_result.csv' % name, scraped)
            dump_json('%s_result.json' % name, scraped)
            dump_log('debug.json', debug)

    except KeyboardInterrupt: 
        pass

if __name__ == '__main__':
    main()

