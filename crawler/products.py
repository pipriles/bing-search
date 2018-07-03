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
            json.dump(self.result, f, indent=4)

    # Not yet implemented
    def dump_csv(self, filename):
        columns = [ 'url', 'vendor', 'type', 'key' ]
        df = pd.DataFrame(self.result)
        df[columns].to_csv(filename, index=None)

def main():
    keywords = ["teelaunch", "pillow profits", "printify", 
        "printful", "gotten", "customcat", "custom cat", 
        "viralstyle", "gooten", "kite", "scalable press", 
        "gearlaunch", "isikel" ]

    filename = './bruno.csv'
    df = pd.read_csv(filename, index_col=False)
    websites = df.iloc[:,1] # Shop domain
    websites = websites[websites != 'REDACTED']
    websites = websites.drop_duplicates()
    websites = websites.apply(prepare_url)

    # Test if website is not down
    # Then try to crawl it
    # -
    # Assume page is up if there was a
    # error skip that url

    try:
        spider = ShopifySpider(keywords)
        spider.scrape_websites(websites)
    except KeyboardInterrupt: pass
    finally:
        spider.dump_json('pages.json')
        spider.dump_csv('pages.csv')

if __name__ == '__main__':
    main()