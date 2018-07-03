#!/usr/bin/env python3

from urllib.parse import urljoin
import requests as rq
import json
import re

from bs4 import BeautifulSoup

HEADERS = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36', 'accept-language': 'en' }

def search_key(url,key):
    product_urls = []
    params = {'q':'"'+key+'"'}

    res = rq.get(url,params=params,headers=HEADERS,timeout=5)
    if res.ok:
        soup = BeautifulSoup(res.text,"html.parser")
        anchor = soup.select("a")
        hrefs = list(map(lambda x: x.get('href'),anchor))
        hrefs = list(set(hrefs))
        hrefs = list(filter(lambda x: x != None,hrefs))
        products = list((filter(lambda x: re.match(r'\/products\/',x),hrefs)))

        for product in products:
            product_urls.append(urljoin(url, product))

    else: print(res.status_code)

    return product_urls

def scrape_product(product_urls, key):

    info = []
    mregex = re.compile(
        r'var meta = {"product":{"id":[^,]*,"vendor":"([^"]*)","type":"([^"]*)',
        flags=re.I 
    )

    for ur in product_urls:
        res = rq.get(ur, headers=HEADERS, timeout=5)
        if res.ok:
            rex = r'(?:^|[^a-zA-Z]){}(?:$|[^a-zA-Z])'.format(key)
            match = re.search(rex, res.text, flags=re.I)
            if match:
                meta = mregex.search(res.text)
                if meta: 
                    info.append({ 'url': ur, 'vendor': meta.group(1), 
                        'type': meta.group(2), 'key': key })
                break
        else: 
            print(res.status_code)

    return info

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
            try:
                product_urls = search_key(url,key)
                total += scrape_product(product_urls, key)
            except Exception as e:
                print(e)
        write_json(total)
    return total

def main():
    try:
        keywords = ["teelaunch", "pillow profits", "printify", "printful", 
            "gotten", "customcat", "custom cat", "viralstyle", 
            "gooten", "kite", "scalable press", "gearlaunch", "isikel"]

        urls = load_url("bruno.in") # Fucking pandas
        total = scrape(keywords, urls)
        write_json(total)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
