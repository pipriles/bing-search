#!/usr/bin/env python3
# Last True url index

import urllib
import pandas as pd

from urllib.parse import urlparse

def hostname(url):
    parsed = urlparse(url)
    return parsed.hostname

df = pd.read_csv("../websites/TOTAL.csv", dtype=str)
websites = df['Domain']

found = pd.read_csv("total.csv", dtype=str)
found = found['url'].drop_duplicates()
found = found.apply(hostname)

s = websites.isin(found)
index = s.index[s][-1] 

print(index, websites[index])

