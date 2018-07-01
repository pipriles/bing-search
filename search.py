import requests as rq
import re

from bs4 import BeautifulSoup

def scrape_google(params={},headers={}):
	url = "https://www.google.com/search"
	resp = rq.get(url, params=params, headers=headers)
	print("google")
	log(resp.text)
	html = resp.text
	soup = BeautifulSoup(html, 'html.parser') 

	anchors = soup.select("h3.r a")
	snippets = soup.select("span.st")

	for a, p in zip(anchors, snippets):
		yield { 'url': a['href'], 'name': a.get_text(),'snippet': p.get_text() }

def scrape_metacrawler(params={},headers={}):
	url = "https://www.metacrawler.com/search/web"
	resp = rq.get(url, params=params, headers=headers)
	exp = r'"display_url":"([^,]*),"title":"([^"]*)","description":"([^"]*)","url":"[^"]*","position":[^,]*,"paid":[^,]*,[^,]*,"type":"([^"]*)"'
	print("meta")
	log(resp.text)
	html = resp.text
	match = match = re.findall(exp,html)
	anchors_and_snippets = list(filter(lambda x: x[3]=="web",match))

	for an in anchors_and_snippets:
		yield { 'url': an[0], 'name': an[1],'snippet': an[2] }

def scrape_bing(params={},headers={}):
	url = 'https://www.bing.com/search'
	resp = rq.get(url, params=params, headers=headers)
	print("bing")
	log(resp.text)
	html = resp.text
	soup = BeautifulSoup(html, 'html.parser')
	anchors = soup.select('#b_results li.b_algo a') 
	snippets = soup.select('#b_results li.b_algo p')

	for a, p in zip(anchors, snippets):
		yield { 'url': a['href'], 'name': a.get_text(),'snippet': p.get_text() }

def log(html):
	with open("log.html","w") as f:
		f.write(html)


def scrape_site():
	scrapes = [scrape_bing,scrape_google,scrape_metacrawler]
	i = 0

	while True:
		i = i % 3
		yield scrapes[i]
		i += 1
