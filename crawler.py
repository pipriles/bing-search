#!/usr/bin/env python3

import requests as rq
import bs4
import re
import pprint

def uncomment_soup(html):
    # Not satisfied with this solution
    uncommented = re.sub(r'(?:<!--)|(?:-->)', '', html)
    soup = bs4.BeautifulSoup(uncommented, 'html5lib') # Very slow
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

def main():
    # url = 'https://trendygear.us/search?q=%22teelaunch%22'
    url = 'https://www.rageon.com/a/search?q="printful"'
    resp = rq.get(url)
    html = resp.text
    pp = pprint.PrettyPrinter()

    result = product_hrefs(html)
    pp.pprint(result)

if __name__ == '__main__':
    main()

