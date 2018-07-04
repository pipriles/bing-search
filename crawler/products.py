#!/usr/bin/env python3
# We have to check those with error
# So we can check if that's another site that has 
# a shop under the same domain
# Maybe we should change the timeout to 2 seconds

import requests as rq
import json
import re
import pandas as pd
import sys
import os
import threading
import queue

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
    params = { 'q': '"{}"'.format(key) }

    res = rq.get(url, params=params, **kwargs)
    res.raise_for_status() # Raise exception if there was an error

    html = res.text

    # List comprehension FTW
    # ----------------------
    # soup = BeautifulSoup(html,"html.parser")
    #
    # anchor = soup.select("a")
    # hrefs = [ x.get('href') for x in anchor ]
    # hrefs = list(set(hrefs))
    # hrefs = [ x for x in hrefs if not x is None ]
    #
    # products = [ x for x in hrefs if re.match(r'\/products\/', x) ]
    # ----------------------

    # Wink wink (Heuristic)
    products = product_hrefs(html)

    for product in products:
        product_urls.append(urljoin(url, product))

    return product_urls

def scrape_products(product_urls, key):

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
        break

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
    result = list(dict.fromkeys(result)) # Remove duplicates
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

class ShopifySpider:

    """ Search for keywords inside a shop """

    def __init__(self, keywords):
        self.keywords = keywords 
        self.result = []
        self._count = 0

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
            message = '- %s:' % k
            try:
                products = search_key(url, k)
                print(message, len(products))

            except rq.exceptions.HTTPError as e:
                print(message, '%s...' % str(e)[:16])
                break

            except Exception as e:
                print(message, '%s...' % str(e)[:73])
                continue

            # Max 2 first products
            self.scrape_products(products, k, 2)

        # Report how much was scraped so far
        print('%s found\n' % len(self.result))
        self._count += 1

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
            json.dump(self.result, f, indent=4)
            print('JSON dumped')

    # Not yet implemented
    def dump_csv(self, filename):
        if not self.result: return 
        columns = [ 'url', 'vendor', 'type', 'key' ]
        df = pd.DataFrame(self.result)
        df[columns].to_csv(filename, index=None)
        print('CSV Dumped')

    def dump_scraped(self, filename):
        print('TOTAL SCRAPED: ', self._count)
        with open(filename, 'w', encoding='utf8') as f: 
            count = str(self._count)
            f.write(count)

class SpiderThread(threading.Thread):

    """ Scrape url with multiple threads """

    def __init__(self, spider, _queue):
        threading.Thread.__init__(self)
        self._spider = spider
        self._queue = _queue
        self._alive = True

    def run(self):
        while self._alive:
            item = self._queue.get()

            # If it is None it is poison
            if item is None: break 

            # Then it should be an url
            print('Processing', item)
            self._spider.search_keywords(item)
            self._queue.task_done()

        print('Thread closed!')

def crawl_websites(websites, spider, N=1):

    _queue = queue.Queue()
    workers = []

    for x in range(N):
        s = SpiderThread(spider, _queue)
        s.start()
        workers.append(s)

    for url in websites: _queue.put(url)

    # Close it
    for w in workers: _queue.put(None)
    for w in workers: w.join()

def hostname(url):
    url = add_scheme(url, 'http')
    url = urlparse(url)
    return url.hostname

def remove_found(filename, websites):

    try:
        df = pd.read_csv(filename)
        black = df.iloc[:,0] # Assume first column has the websites
        black = websites.apply(hostname)
        black = websites.drop_duplicates()
        found = websites.isin(black)
        print(found)
        return websites[~found]

    except FileNotFoundError: 
        return websites

def main():
    keywords = ["teelaunch", "pillow profits", "printify", 
        "printful", "gotten", "customcat", "custom cat", 
        "viralstyle", "gooten", "kite", "scalable press", 
        "gearlaunch", "isikel" ]

    if len(sys.argv) != 2:
        print('Usage: ./products.py [FILENAME]')
        return

    filename = sys.argv[1]
    df = pd.read_csv(filename, index_col=False)
    websites = df['Domain']
    websites = websites.drop_duplicates()
    websites = websites.apply(prepare_url)

    # Remove blacklisted, it reads as csv
    websites = remove_found('blacklist.in', websites)

    try:
        spider = ShopifySpider(keywords)
        # spider.scrape_websites(websites)
        crawl_websites(websites, spider, N=12)
    except KeyboardInterrupt: pass
    finally:
        name = os.path.basename(filename)
        name = os.path.splitext(name)[0]
        spider.dump_json('%s_result.json' % name)
        spider.dump_csv('%s_result.csv' % name)
        spider.dump_scraped('debug')
        # I should probably kill the spider workers
        # too more gracefully

if __name__ == '__main__':
    main()
