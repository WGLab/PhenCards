# use kegg API to get data

import requests
from bs4 import BeautifulSoup
import sys
import xml.etree.ElementTree as ET
import time
from lib.json import format_json_table
from lib.style import generate_headers
from json2html import json2html
import re
from collections import defaultdict
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
            for i in results[domain]:
                i['chi_square'] = str(round(float(i['chi_square']),2))
        else:
            results[domain] = []


    conditions = results['Condition']
    drugs = results['Drug']
    procedures = results['Procedure']
    headers=generate_headers()
    headers={"COHDC": headers['COHDC'], "COHDA": headers['COHDA']}
    return ancestors, conditions, drugs, procedures, headers

# pathway page generator

def kegg_page(phenname):
    phenname=phenname.replace("_", "+").replace(" ","+")
    diseases=requests.get('http://rest.kegg.jp/find/disease/'+phenname, verify=False, stream=True)
    diseases=[x.split("\t") for x in diseases.text.strip().split("\n")]
    paths = defaultdict(list)
    for did, dname in diseases:
        path=requests.get('http://rest.kegg.jp/link/pathway/'+did, verify=False, stream=True)
        for line in path.text.splitlines():
            if re.search("hsa", line):
                paths[line.strip().split("\t")[1]].append(dname)
    # generate temporary images then os remove using @after_this_request decorator in flask under app route (/results/pathway)
    dispath = {}
    print (paths)
    for i, pid in enumerate(paths):
        link='https://www.genome.jp/dbget-bin/www_bget?'+pid
        reqname=requests.get('http://rest.kegg.jp/get/'+pid, verify=False, stream=True)
        for line in reqname.text.splitlines():
            if re.search("NAME\s*", line):
                name=re.split("\w*\s*",line,1)[-1].split("-")[0]
        dispath[name]=[paths[pid],link]
    headers=generate_headers()
    headers={"KEGG": headers['KEGG']}

    return dispath, headers

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
    headers=generate_headers()
    headers={"Pubmed": headers['Pubmed']}
    return pubmed, headers

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

    headers=generate_headers()
    headers={"Tocris": headers['Tocris']}
    return drugs, headers

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

    headers=generate_headers()
    headers={"APEX": headers['APEX']}
    return drugs, headers

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
        payload = "&".join("%s=%s" % (k,v) for k,v in params.items()) # prevents URL encoding of "+"
        clinicaljson = requests.get('https://clinicaltrials.gov/api/query/study_fields', params=payload, verify=False)
        print (clinicaljson.url)
        clinicaljson = clinicaljson.json()['StudyFieldsResponse']
    except:
        clinicaljson = {}

    headers=generate_headers()
    headers={"Clinical": headers['Clinical']}
    return clinicaljson, headers

# phen2gene api call
def phen2gene_page(HPOquery, patient=False):
    if patient: 
        HPOquery=";".join(HPOquery)
    params = {
    'HPO_list': HPOquery,
    'weight_model': 'sk'}
    try:
        GeneAPI_JSON = requests.get('https://phen2gene.wglab.org/api', params=params, verify=False)
        print (GeneAPI_JSON.url,file=sys.stderr)
        GeneAPI_JSON = GeneAPI_JSON.json()['results'][:1000]
    except Exception as e:
        GeneAPI_JSON = {}
        print (e)

    return GeneAPI_JSON

def patient_page(HPOquery, HPO_names):
    HPOclinical="+OR+".join([s.replace(" ", "+") for s in HPO_names])
    phen2gene_table = phen2gene_page(HPOquery,patient=True)

    return HPOclinical, phen2gene_table

def umls_auth(user="username", password="wouldntyoulovetoknow"):
    data = {"licenseCode": "NLM-323530719", # from uts profile
            "user": user, # from user input
            "password": password} # from user input
    try:
        response = requests.post("https://uts-ws.nlm.nih.gov/restful/isValidUMLSUser", data=data)
        if response.status_code == 200:
            if "true" in response.text:
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        print (e)
        return False
