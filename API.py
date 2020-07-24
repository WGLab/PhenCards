# use kegg API to get data

import requests
from bs4 import BeautifulSoup
import sys

# input is the phenotype name, output is list([reference w/ external links])


def tocris_drugs_api(query):
    link = "https://www.tocris.com/search?keywords=" + query
    html_doc = requests.get(link, verify=False).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    drugs = []
    for item in soup.find_all('a'):
        item = str(item)
        if item and item.startswith('<a class="search_link" data-brand="tocris"'):
            idx = item.find('href="') + 6
            item = item[:idx] + "https://www.tocris.com/" + item[idx+1:] #+1 removes extra slash
            drugs.append(item)
    return drugs


# print(tocris_drugs_api("cleft palate"))

def apexbt_drugs_api(query):
    link = "https://www.apexbt.com/catalogsearch/result/?q=" + query
    html_doc = requests.get(link, verify=False).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    drugs = []
    for item in soup.find_all('a'):
        item = str(item)
        if item and item.startswith('<a href="https://www.apexbt.com/') and '<span class="product-list-name"' in item:
            link=item.split("\"")[1]
            drug=item.split("<span class=\"product-list-name\">")[1].split("<")[0]
            drugs.append([link,drug])
            
    return drugs


# print(apexbt_drugs_api("cleft palate"))
