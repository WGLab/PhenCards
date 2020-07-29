# use kegg API to get data

import requests
from bs4 import BeautifulSoup
import sys
import xml.etree.ElementTree as ET
import time
from lib.json import format_json_table
from json2html import json2html
import json

# cohd list generator
def generate_cohd_list(HPOquery):
    HPOquery=HPOquery.replace("+","_") # replace + with _
    params={
    'q': HPOquery,
    'dataset_id': 4, # lifetime non-hierarchical is 2, 4 is temporal beta
    'domain': "Condition", # can use "Drug" for drugs
    'min_count': 1
    }
    rsearch=requests.get("http://cohd.io/api/omop/findConceptIDs", params=params)
    if rsearch.status_code == requests.status_codes.codes.OK:
        results = rsearch.json()
        results=sorted(results['results'], key=lambda k: k['concept_count'], reverse=True)
    else:
        results = []

    return results

# cohd page generator
def cohd_page(concept_id):
    params={
        'concept_id': concept_id,
        'dataset_id': 4, # lifetime non-hierarchical is 2, 4 is temporal beta
    }
    rsearch=requests.get("http://cohd.io/api/omop/conceptAncestors", params=params)
    if rsearch.status_code == requests.status_codes.codes.OK:
        results = rsearch.json()
        ancestors = sorted(results['results'], key=lambda k: k['concept_count'], reverse=True)
    else:
        ancestors = []
    domains = ['Drug', 'Condition', 'Procedure']
    results={}
    for domain in domains: 
        params={
            'concept_id_1': concept_id,
            'dataset_id': 4, # lifetime non-hierarchical is 2, 4 is temporal beta
            'domain': domain, # get the drugs, conditions, etc.
        }
        rsearch=requests.get("http://cohd.io/api/association/chiSquare", params=params)
        if rsearch.status_code == requests.status_codes.codes.OK:
            results[domain] = rsearch.json()
            results[domain] = sorted(results[domain]['results'], key=lambda k: k['chi_square'], reverse=True)
        else:
            results[domain] = []


    conditions = results['Condition']
    drugs = results['Drug']
    procedures = results['Procedure']
    return ancestors, conditions, drugs, procedures

# pubmed page generator
def literature_page(HPOquery):
    pubmed={}
    params1={
    'db': 'pubmed',
    'term': HPOquery,
    'retmax': '200',
    'sort': 'relevance'}
    rsearch=requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params1)
    def generate_citations(uid):
        params2={
        'retmode': "json",
        'dbfrom': "pubmed",
        'db': "pubmed",
        'linkname': "pubmed_pubmed_citedin",
        'id': uid, # get from esearch
        'cmd': "neighbor",
        'api_key': '1ee2a8a8bf1b1b2b09e8087eb5cf16c95109'
        }
        while True:
            rsearch=requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi", params=params2)
            rdict=rsearch.json()
            try:
                links = rdict['linksets'][0]['linksetdbs'][0]['links']
                citedby = len(links)
                return citedby
            except KeyError as e:
                e='{}: {}'.format(type(e).__name__, e)
                if 'linksetdbs' in e:
                    return 0
                else:
                    time.sleep(0.1)
                   # print (e,uid, "time", file=sys.stderr)
            except Exception as e:
                print (e,uid,"exc",file=sys.stderr)
                return 0
        return 0

    root=ET.fromstring(rsearch.text)
    ids={}
    for i in root.iter("Id"):
        citedby=generate_citations(i.text)
        ids[i.text]=citedby
    top25=sorted(ids, key=ids.get, reverse=True)[:25]
    top25 = { key: ids[key] for key in top25 }

    query=",".join(top25.keys())
    rsum=requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id="+query+"&retmode=text&rettype=abstract")
    root=ET.fromstring(rsum.text)
    title=pages=first=authors=pubdate=doi=volume=issue=''
    for doc in root.iter("DocSum"):
        id1 = doc.find("Id").text
        for child in doc.iter("Item"):
            if child.attrib['Name'] == "AuthorList":
                if child:
                    g = child[0]
                    first=g.text
            if child.attrib['Name'] == "LastAuthor":
                authors=child.text
            if child.attrib['Name'] == "Title":
                title=child.text
            if child.attrib['Name'] == "Source":
                journal=child.text
            if child.attrib['Name'] == "PubDate":
                pubdate=child.text
            if child.attrib['Name'] == "Volume":
                if child.text:
                    volume = ";"+child.text
            if child.attrib['Name'] == "Issue":
                if child.text:
                    issue="("+child.text+")"
            if child.attrib['Name'] == "Pages":
                if child.text:
                    pages=":"+child.text
            if child.attrib['Name'] == "DOI":
                doi="doi:"+child.text
        if authors and first != authors:
            authors = first + " .. " + authors
        else:
            authors = first
        if title:
            publication = title + " " + authors + ". " + journal + " " + pubdate + volume + issue + pages + ". " + doi
        pubmed[id1]=[publication,top25[id1]]
    return pubmed

# tocris drugs page generator
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

    drugs = format_json_table(drugs, 'DRUG')
    drugs = json2html.convert(json=drugs,
          table_attributes="id=\"results-drugs\" class=\"table table-striped table-bordered table-sm\"",
          escape=False)
    return drugs

# apexbio page generator
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

# clinical trial page generator
def clinical_page(HPOquery):
    try:
        fields = [
        "NCTId",
        "BriefTitle",
        "Condition",
        "InterventionName"]
        params = {
        'expr': HPOquery,
        'fields': ','.join(fields),
        'min_rnk': '1',
        'max_rnk': '1000',
        'fmt': 'json'}
        clinicaljson = requests.get('https://clinicaltrials.gov/api/query/study_fields', params=params, verify=False)
        clinicaljson = clinicaljson.json()['StudyFieldsResponse']#?expr='+ HPOquery +'&fields=NCTId%2CBriefTitle%2CCondition%2CInterventionName&min_rnk=1&max_rnk=1000&fmt=json', verify=False).json()['StudyFieldsResponse']
        print (clinicaljson)
    except:
        clinicaljson = {}
    return clinicaljson

# phen2gene api call
def phen2gene_page(HPOquery, patient=False):
    if patient: 
        HPOquery=";".join(HPOquery)
    params = {
    'HPO_list': HPOquery,
    'weight_model': 'sk'}
    try:
        GeneAPI_JSON = requests.get('https://phen2gene.wglab.org/api', params=params, verify=False)
        print (GeneAPI_JSON.url)
        GeneAPI_JSON = GeneAPI_JSON.json()['results'][:1000]
        print (GeneAPI_JSON)
        #GeneAPI_JSON = json.loads(GeneAPI_JSON)[:1000]
    except Exception as e:
        GeneAPI_JSON = {}
        print (e)

    p2g_table = json2html.convert(json=GeneAPI_JSON,
                    table_attributes="id=\"phen2gene-api\" class=\"table table-striped table-bordered table-sm\"")
    return p2g_table
