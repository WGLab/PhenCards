# use kegg API to get data

import requests
from bs4 import BeautifulSoup


# input is the phenotype name, output is list([reference w/ external links])
def kegg_api_reference(name):
    link = "http://rest.kegg.jp/find/disease/" + name.replace(' ', '+')
    # get the ID
    kegg_id = requests.get(link, verify=False).text[:9]
    link = "http://rest.kegg.jp/get/" + kegg_id
    res = requests.get(link, verify=False).text.splitlines()
    reference = []
    for i in range(len(res)):
        item = res[i]
        if item.startswith('REFERENCE'):
            reference.append(res[i:i + 5])
    res = ''
    hyper = 'https://www.ncbi.nlm.nih.gov/pubmed/'
    for ref in reference:
        for i in range(len(ref)):
            item = ref[i]
            if item.startswith('REFERENCE'):
                ref[i] = 'REFERENCE ' + '<a href=' + hyper + item[17:] + '>' + item[12:] + '</a>'
        ref = '\n'.join(ref)
        res += ref + '\n\n'
    return res


# print(kegg_api_reference('cleft palate'))


def kegg_api_drug(name):
    link = "http://rest.kegg.jp/find/disease/" + name.replace(' ', '+')
    # get the ID
    kegg_id = []
    for ds in (requests.get(link, verify=False).text.split('\n')):
        kegg_id.append(ds[:9])
    kegg_set = set(kegg_id[:-1])
    link = "http://rest.kegg.jp/link/drug/disease"
    match = requests.get(link, verify=False).text.splitlines()
    dr = 'dr:D01031'
    # print(kegg_set)
    for record in match:
        if record[:9] in kegg_set:
            dr = record[10:]
            break
    link = "http://rest.kegg.jp/get/" + dr
    text = requests.get(link, verify=False).text.splitlines()
    return text


# print(kegg_api_drug('cleft palate'))


def apexbt_drugs_api(name):
    link = "https://www.tocris.com/search?keywords=" + name.replace(' ', '+')
    html_doc = requests.get(link, verify=False).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    drugs = []
    for item in soup.find_all('a'):
        item = str(item)
        if item and item.startswith('<a class="search_link" data-brand="tocris"'):
            idx = item.find('href="') + 6
            item = item[:idx] + "https://www.tocris.com/" + item[idx:]
            drugs.append(item)
    return '\n'.join(drugs)


# print(apexbt_drugs_api("cleft palate"))
