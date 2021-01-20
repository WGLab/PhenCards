import requests
from bs4 import BeautifulSoup
import sys
import xml.etree.ElementTree as ET
import time
from lib.json import format_json_table
from lib.style import generate_headers
from json2html import json2html
from queries import elasticquery
import re
from collections import defaultdict
import json
import ray
import datetime
import concurrent.futures
import pandas
from pandas.io.sql import read_sql_query
import psycopg2, psycopg2.extras

# drugcentral remote postgresql db

def postgresConnect(dbhost="unmtid-dbs.net", dbport="5433", dbname="drugcentral", dbusr="drugman", dbpw="dosage"):
    """Connect to db; specify default cursor type DictCursor."""
    dsn = ("host='%s' port='%s' dbname='%s' user='%s' password='%s'"%(dbhost, dbport, dbname, dbusr, dbpw))
    dbcon = psycopg2.connect(dsn)
    dbcon.cursor_factory = psycopg2.extras.DictCursor
    return dbcon

def dbVersion(dbcon, dbschema="public"):
    sql = f"SELECT * FROM {dbschema}.dbversion"
    cur = dbcon.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(sql)
    ver = cur.fetchall()[0]
    version = "Version: "+str(ver[0])+"; Datetime: "+ver[1].strftime("%m/%d/%Y, %H:%M:%S")
    return version

def listTables(dbcon, dbschema="public"):
    '''Listing the tables.'''
    sql = (f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{dbschema}'")
    df = read_sql_query(sql, dbcon)
    return df

def listColumns(dbcon, dbschema="public"):
    df=None;
    sql1 = (f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{dbschema}'")
    df1 = read_sql_query(sql1, dbcon)
    for tname in df1.table_name:
        df=None
        sql2 = (f"SELECT column_name,data_type FROM information_schema.columns WHERE table_schema = '{dbschema}' AND table_name = '{tname}'")
        df_this = read_sql_query(sql2, dbcon)
        df_this["schema"] = dbschema
        df_this["table"] = tname
        df = df_this if df is None else pandas.concat([df, df_this])
        df = df[["schema", "table", "column_name", "data_type"]]
    return df

def getDrugData(dict):
    dbcon=dict["dbcon"]; query=dict["query"]; column=dict["column"]; tname=dict["tname"]
    HPOquery=query.replace("_"," ").replace("+"," ")
    sql2 = f"SELECT * FROM {tname} WHERE {column} ILIKE '%{HPOquery}%'"
    """
    # faers header:
    "id", 
    "struct_id", 
    "meddra_name", 
    "meddra_code", 
    "level", 
    "llr", 
    "llr_threshold", 
    "drug_ae", 
    "drug_no_ae", 
    "no_drug_ae", 
    "no_drug_no_ae", 
    "name" (added by me)
    # drug use header (omop):
    id      struct_id       concept_id      relationship_name       concept_name    umls_cui        snomed_full_name        cui_semantic_type       snomed_conceptid
    """
    cur = dbcon.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql2)
    data = cur.fetchall()
    df = []
    for dictrow in data:
        if dictrow:
            dictrow.pop('id', None); dictrow.pop('meddra_code', None) # for FAERS
            dictrow.pop('snomed_full_name', None); dictrow.pop('cui_semantic_type', None); dictrow.pop('snomed_conceptid', None) # for SNOMED/OMOP
            df.append(dictrow)
    return df

def getDrugInfo(dbcon):
    sql2 = (f"SELECT id, name FROM synonyms WHERE preferred_name = 1.0")
    cur = dbcon.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(sql2)
    data = cur.fetchall()
    drugnames = {}
    for dictrow in data:
        if dictrow:
            drugnames[dictrow[0]]=dictrow[1] # set id key, name value
    df = read_sql_query(sql2, dbcon)
    return drugnames

def getDrugDDIs(drugname):
    dbcon = postgresConnect()
    ddis = getDrugData({"dbcon":dbcon, "query":drugname, "column":"drug_class1", "tname":"ddi"})
    return ddis.to_dict()

def DrugCentral(HPOquery):
    dbcon = postgresConnect()
    df2 = getDrugInfo(dbcon)
    version = dbVersion(dbcon)
    # listTables(dbcon, fout=output)
    # listColumns(dbcon, fout=output)
    dfs = {}
    dicts = [
            (getDrugData, {"dbcon":dbcon, "query":HPOquery, "column":"meddra_name", "tname":"faers_male"}),
            (getDrugData, {"dbcon":dbcon, "query":HPOquery, "column":"meddra_name", "tname":"faers_female"}),
            (getDrugData, {"dbcon":dbcon, "query":HPOquery, "column":"concept_name", "tname":"omop_relationship"}),
            ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_data = {executor.submit(func, dict): dict for func, dict in dicts}
        for future in concurrent.futures.as_completed(future_to_data):
            data = future_to_data[future]
            print(data['tname'])
            try:
                df = future.result()
                if not df:
                    continue
                dfs[data['tname']] = [list(row.values()) + [df2[row['struct_id']]] for row in df]
            except Exception as exc:
                print('%r generated an exception: %s' % (data, exc))
    # getDrugData(dbcon=dbcon, query="craniosynostosis", column="meddra_name", tname="faers", fout=output)
    # # OMOP
    # getDrugData(dbcon=dbcon, query="craniosynostosis", column="concept_name", tname="omop_relationship", fout=output)
    # # INFO on drug, get ID from above...
    # getDrugInfo(dbcon=dbcon, query="489", column="id", tname="synonyms", fout=output)
    # # DDIs on drug, get name from above...
    # getDrugData(dbcon=dbcon, query="carbamazepine", column="drug_class1", tname="ddi", fout=output)
    return version, dfs

# pharos api 

def pharos(HPOquery, query):
    HPOquery=HPOquery.replace("+"," ")
    url="https://pharos-api.ncats.io/graphql"
    query=query % HPOquery
    r = requests.post(url, json={'query': query})
    data = json.loads(r.text)["data"]

    return data


def pharos_page(HPOquery):
    facetdata = {}
    query = """query facetsForTargetsForDisease {
                  targets(filter: { associatedDisease: "%s" }) {
                    facets {
                      facet
                      dataType
                      values {
                        name
                        value
                      }
                    }
                  }
                }
                """
    data = pharos(HPOquery, query)
    try:
        facets = data["targets"]["facets"]
        #print(json.dumps(facetdata,indent=2)) 
        for facet in facets:
            if facet["facet"] in ["Linked Disease", "Reactome Pathway", "GO Process", "GO Component", "GO Function", "UniProt Disease", "Expression: UniProt Tissue", "Family", "Target Development Level"]:
                    facetdata[facet["facet"]] = facet["values"]
    except:
        facets = {}
    headers=generate_headers()
    headers={"PharosFacets": headers['PharosFacets']}

    return facetdata, headers

def pharos_targets(HPOquery):
    query="""query associatedTargets {
              targets(filter: { associatedDisease: "%s" }) {
                targets(top: 1000) {
                  name
                  uniprot
                  sym
                  diseaseAssociationDetails {
                    name
                    dataType
                    evidence
                  }
                }
              }
            }
            """
    data = pharos(HPOquery, query)
    try:
        targetdata = data["targets"]["targets"]
    except:
        targetdata = {}
    # print(json.dumps(targetdata,indent=2)) 

    return targetdata

def pharos_ppis(gene):
    query="""query interactingProteins {
              targets(filter: { associatedTarget: "%s" }) {
                targets(top: 1000) {
                  name
                  sym
                  ppiTargetInteractionDetails {
                    dataSources: ppitypes
                    score
                    p_ni
                    p_int
                    p_wrong
                  }
                }
              }
            }
            """
    data = pharos(gene, query)
    try:
        ppis = data["targets"]["targets"]
    # print(json.dumps(targetdata,indent=2)) 
    except:
        ppis = {}
    return ppis

def pharos_target_details(gene):
    query="""query targetDetails {
              target(q: { sym: "%s" }) {
                name
                tdl
                fam
                sym
                description
                novelty
                expressions(top: 10000) {
                  type
                  value
                  tissue
                }
                ligands(top: 1000) {
                  ligid
                  name
                  isdrug
                  description
                  activities {
                    moa
                    pubs {
                      pmid
                    }
                  }
                }
              }
            }
            """
    data = pharos(gene, query)
    try:
        targetinfo = data["target"]
        details = {}
        expressions, ligands = [[] for i in range (0,2)]
        for entry in targetinfo:
            if entry in ["name", "tdl", "fam", "sym", "description", "novelty"]:
                details[entry]=targetinfo[entry]
            elif entry == "expressions":
                expressions=targetinfo[entry]
            elif entry == "ligands":
                ligands=targetinfo[entry]
                for ligand in ligands:
                    ligand["pubs"] = ",".join([j["pmid"] for i in ligand["activities"] if i["pubs"] for j in i["pubs"]])
                    # ligand["moa"] = ",".join([str(i["moa"]) for i in ligand["activities"]])
                    del ligand["activities"]
    except:
        details, expressions, ligands = {}, {}, {}
    headers=generate_headers()
    headers={"PharosTD": headers["PharosTD"], "PharosTE": headers["PharosTE"], "PharosTL": headers["PharosTL"], "PharosTP": headers["PharosTP"]}
    # print(json.dumps(targetinfo,indent=2)) 

    ppis = pharos_ppis(gene)

    return details, expressions, ligands, ppis, headers

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
                i['adj_p-value'] = str('{:0.3e}'.format(float(i['adj_p-value'])))
                i['p-value'] = str('{:0.3e}'.format(float(i['p-value'])))
        else:
            results[domain] = []


    conditions = results['Condition']
    drugs = results['Drug']
    procedures = results['Procedure']
    headers=generate_headers()
    headers={"COHDC": headers['COHDC'], "COHDA": headers['COHDA']}
    return ancestors, conditions, drugs, procedures, headers

# kegg page generator

def kegg_page(phenname):
    phenname=phenname.replace("_", "+").replace(" ","+")
    try:
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
    except:
        dispath={}
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
    'api_key': '1ee2a8a8bf1b1b2b09e8087eb5cf16c95109',
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
    
    # print(rsearch.url, file=sys.stderr) if needed to debug...most likely NCBI 500 error

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

def direct2experts(HPOquery):
    experts={}
    params1={
    'request': 'getsites',
    }
    try:
        rsearch=requests.get("http://direct2experts.org/DirectService.asp", params=params1)
        # print(rsearch.url, file=sys.stderr) if needed to debug...most likely 404 or timeout error
    except requests.exceptions.Timeout:
        print ("timedout d2e")
        return "timedout d2e"
    except requests.exceptions.ConnectionError:
        print ("connection refused d2e")
        return "connection refused d2e"
    def generate_numbers(url, HPOquery):
        numexp=0
        searchurl="null"
        try:
            rsearch=requests.get(url+HPOquery, timeout=1.5)
            if rsearch.status_code == 200:
                root=ET.fromstring(rsearch.text)
                numexp=root.find("count").text
                searchurl=root.find("search-results-URL").text
        except requests.exceptions.Timeout:
            print ("timedout", url)
        except requests.exceptions.ConnectionError:
            print ("connection refused", url)
        return numexp, searchurl 

    root=ET.fromstring(rsearch.text)
    for site in root.iter("site-description"):
        name = site.find("name").text
        query = site.find("aggregate-query").text
        numexp, searchurl = generate_numbers(query, HPOquery)
        # print (numexp, searchurl)
        if searchurl == "null":
            continue
        experts[name]=[numexp, searchurl]
    
    headers = generate_headers()
    d2e = {'result': experts}
    d2e['header'] = headers['D2E']
    return d2e

def patient_page(HPOquery, HPO_names, d2hjson):
    HPOclinical = "+OR+".join([s.replace(" ", "+") for s in HPO_names])
    phen2gene_table = phen2gene_page(HPOquery,patient=True)
    headers = generate_headers()
    headers = {"HPOPatient": headers["HPOPatient"], "P2G": headers["P2G"], "PatientDisease": headers["PatientDisease"]}
    linked_diseases = disease_table(d2hjson)

    return HPOclinical, phen2gene_table, headers, linked_diseases

def disease_table(d2hjson):
    results = defaultdict(float)
    for HPOquery in d2hjson:
        # print(HPOquery, file=sys.stderr)
        # {'hpoId': 'HP:0000664', 'hpoName': 'synophrys', 'length': 9, 'negated': True, 'start': 48}
        if HPOquery['negated']:
            continue
        eresults=elasticquery(HPOquery['hpoName'], 'hpolink', esettings="diseases")['result']
        for eresult in eresults:
            results[eresult['_source']['NAMEEXACT']]+=eresult['_score']

    return results

def umls_auth(ticket):
    params = {"service": "https://phencards.org/umls", # from uts profile
            "ticket": ticket} # from user input
    payload = "&".join("%s=%s" % (k,v) for k,v in params.items()) # prevents URL encoding of "+"
    try:
        response = requests.get("https://uts-ws.nlm.nih.gov/rest/isValidServiceValidate", params=payload)
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

# pathway commons page generator

def pcommons_page(HPOquery):
    try:
        params = {
        'q': HPOquery, # needs "+" for spaces or %20
        'type': "Pathway",
        'organism': "Homo+sapiens",
        'page': 0} # default, gives first page only, max 100 hits per page, would have to manually go page by page to see all results. top 100 is fine in my opinion, though I wrote code to grab it all just in case
        payload = "&".join("%s=%s" % (k,v) for k,v in params.items()) # prevents URL encoding of "+"
        pathjson = requests.get('https://www.pathwaycommons.org/pc2/search.json', params=payload, verify=False)
        pathjson = pathjson.json()
        numHits = pathjson['numHits']
        maxHits = pathjson['maxHitsPerPage']
        pathways = pathjson['searchHit']
        count = 0
        while numHits - count*100 > maxHits:
            count+=1
            params['page']+=1
            payload = "&".join("%s=%s" % (k,v) for k,v in params.items()) # prevents URL encoding of "+"
            pathjson = requests.get('https://www.pathwaycommons.org/pc2/search.json', params=payload, verify=False)
            print (pathjson.url, params)
            pathjson = pathjson.json()
            pathways.extend(pathjson['searchHit'])
            
    except:
        pathways = []
    
    headers=generate_headers()
    # 'uri' for link, 'name' for pathway, 'pathway' for ancestral paths, 'numParticpants', 'numProcesses'
    headers={"PCommons": headers['PCommons']}
    return pathways, headers

def generate_nihfoa_list(HPOquery):
    params={
    'query': HPOquery,
    'type': "active",
    }
    # need to add https://grants.nih.gov/grants/guide/pa-files/results['filename']
    rsearch=requests.get("https://search.grants.nih.gov/guide/api/data", params=params)
    if rsearch.status_code == requests.status_codes.codes.OK:
        results = rsearch.json()['data']['hits']['hits']
        #print(results[0]["_source"].keys()) # we want 'title', 'docnum', 'primaryIC', 'sponsors', 'opendate', 'appreceiptdate', 'expdate' 'filename'
        results=sorted(results, key=lambda k: k['_score'], reverse=True)
    else:
        results = []

    return results

def generate_nihreporter_list(HPOquery):
    now = datetime.datetime.now()
    years = ",".join(map(str,range(now.year-5,now.year+1)))
    params={
    'query': "text:" + HPOquery + "$fy:" + years,
    'searchMode': "Smart",
    }
    payload = "&".join("%s=%s" % (k,v) for k,v in params.items())
    # https://api.federalreporter.nih.gov/v1/projects/search?query=text:cleft+palate$fy:2015,2016,2017,2018,2019,2020&searchMode=Smart
    rsearch=requests.get("https://api.federalreporter.nih.gov/v1/projects/search", params=payload)
    if rsearch.status_code == requests.status_codes.codes.OK:
        results = rsearch.json()['items']
        #print(results[0].keys())
    else:
        results = []

    return results

@ray.remote
def reaction_synonyms(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200920])+AND+"+HPOquery,
    'count': "patient.reaction.reactionmeddrapt.exact",
    }
    synonyms = openfda_query(params)

    return synonyms

@ray.remote
def drugs_causing_reaction(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200920])+AND+"+HPOquery,
    'count': "patient.drug.openfda.generic_name.exact",
    }
    drugs = openfda_query(params)

    return drugs

@ray.remote
def forms_causing_reaction(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200920])+AND+"+HPOquery,
    'count': "patient.drug.drugdosageform.exact",
    }
    forms = openfda_query(params)

    return forms

@ray.remote
def weight_at_reaction(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200920])+AND+"+HPOquery,
    'count': "patient.patientweight",
    }
    weights = openfda_query(params)

    return weights

@ray.remote
def outcomes_of_reaction(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200920])+AND+"+HPOquery,
    'count': "patient.reaction.reactionoutcome",
    }
    outcomes = openfda_query(params)
    for i, outcome in enumerate(outcomes):
        if outcome["term"] == 6:
            outcomes[i]["term"] = "Unknown"
        elif outcome["term"] == 1:
            outcomes[i]["term"] = "Recovered/resolved"
        elif outcome["term"] == 2:
            outcomes[i]["term"] = "Recovering/resolving"
        elif outcome["term"] == 3:
            outcomes[i]["term"] = "Not recovered/not resolved"
        elif outcome["term"] == 4:
            outcomes[i]["term"] = "Recovered/resolved with sequelae (consequent health issues)"
        elif outcome["term"] == 5:
            outcomes[i]["term"] = "Fatal"

    return outcomes

@ray.remote
def ages_at_reaction(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200920])+AND+"+HPOquery,
    'count': "patient.patientagegroup",
    }
    ages = openfda_query(params)
    for i, age in enumerate(ages):
        if age["term"] == 6:
            ages[i]["term"] = "Elderly"
        elif age["term"] == 1:
            ages[i]["term"] = "Neonate"
        elif age["term"] == 2:
            ages[i]["term"] = "Infant"
        elif age["term"] == 3:
            ages[i]["term"] = "Child"
        elif age["term"] == 4:
            ages[i]["term"] = "Adolescent"
        elif age["term"] == 5:
            ages[i]["term"] = "Adult"

    return ages

@ray.remote
def routes_at_reaction(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200920])+AND+"+HPOquery,
    'count': "patient.drug.openfda.route.exact",
    }
    routes = openfda_query(params)

    return routes

@ray.remote
def drugs_for_indication(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200922])+AND+patient.drug.drugindication:"+HPOquery,
    'count': "patient.drug.openfda.generic_name.exact",
    }
    drugi = openfda_query(params)

    return drugi

@ray.remote
def reactions_for_indication(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200922])+AND+patient.drug.drugindication:"+HPOquery,
    'count': "patient.reaction.reactionmeddrapt.exact",
    }
    reactioni = openfda_query(params)

    return reactioni

@ray.remote
def routes_for_indication(HPOquery):
    params={
    'search': "(receivedate:[20040101+TO+20200922])+AND+patient.drug.drugindication:"+HPOquery,
    'count': "patient.drug.openfda.route.exact",
    }
    routei = openfda_query(params)

    return routei

def openfda_query(params):
    payload = "&".join("%s=%s" % (k,v) for k,v in params.items())
    rsearch=requests.get("https://api.fda.gov/drug/event.json", params=payload)
    print(rsearch.url)
    if rsearch.status_code == requests.status_codes.codes.OK:
        results = rsearch.json()['results']
        #print(results[0].keys()) 
    else:
        results = []

    return results

def openfda_page(HPOquery):

    # can also get individual patient queries WITHOUT using count like https://api.fda.gov/drug/event.json?search=(patient.drug.drugindication:"cleft+palate")ANDpatient.drug.openfda.generic_nameANDpatient.reaction.reactionmeddrapt.exact&limit=10
    ray.init()
    func=[reaction_synonyms, drugs_causing_reaction, forms_causing_reaction, weight_at_reaction, outcomes_of_reaction, ages_at_reaction, routes_at_reaction, drugs_for_indication, reactions_for_indication, routes_for_indication]
    sy=func[0].remote(HPOquery)
    dr=func[1].remote(HPOquery)
    fr=func[2].remote(HPOquery)
    wt=func[3].remote(HPOquery)
    ot=func[4].remote(HPOquery)
    ag=func[5].remote(HPOquery)
    rt=func[6].remote(HPOquery)
    dri=func[7].remote(HPOquery)
    rei=func[8].remote(HPOquery)
    rti=func[9].remote(HPOquery)
    synonyms, drugs, forms, weights, outcomes, ages, routes, drugi, reactioni, routei = ray.get([sy, dr, fr, wt, ot, ag, rt, dri, rei, rti])
    headers=generate_headers()
    headers={"OpenFDA": headers['OpenFDA']}
    ray.shutdown()

    return synonyms, drugs, forms, weights, outcomes, ages, routes, drugi, reactioni, routei, headers

