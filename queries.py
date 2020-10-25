from flask import session, request, Response, abort
import sqlite3
from collections import defaultdict
from json2html import json2html
import json
import requests
import sys
from config import Config
import API

from lib.esQuery import indexquery
from lib.style import generate_headers

def connect_to_db(path_to_db):

    # connect to SQLite at phenotype db file
    conn = sqlite3.connect(path_to_db, check_same_thread=False)
    # connect to PHENBASE
    c1 = conn.cursor()
    # connect to ICD10BASE
    c2 = conn.cursor()

    return c1, c2

def doc2hpo(doc2hpo_notes):
    HPO_list = set()
    HPO_names = set()
    HPO_results = {}
    # default doc2hpo text
    if not doc2hpo_notes:
        doc2hpo_notes=Config.doc2hpo_default

    # data to be sent to api 
    data = {
        "note": doc2hpo_notes,
        "negex": True  # default true for now
    }
    DOC2HPO_URL = Config.doc2hpo_url
    r = requests.post(url=DOC2HPO_URL, json=data)

    # check if doc2hpo request is successful
    # if status code of response starts with 2, it is successful, otherwise something is wrong with doc2hpo
    print ("hi", r.status_code, file=sys.stderr)
    if int(str(r.status_code)[:1]) != 2:
        r = requests.post(url='http://127.0.0.1:8000/doc2hpo/parse/acdat', json=data)
        if int(str(r.status_code)[:1]) != 2:
            doc2hpo_error = "Doc2Hpo service is temporarily unavailable and cannot process clinical notes. Please manually input HPO terms instead."
            flash(doc2hpo_error)
            return redirect(url_for('phencards'))
    
    res = r.json()
    print ("results", res, file=sys.stderr)
    res = res["hmName2Id"] # where hpo term result is grabbed

    HPO_set = set()
    HPO_nset = set()
    negated_HPOs = set()
    negated_names = set()

    for i in res:
        if i["negated"]:
            negated_HPOs.add(i["hpoId"])
            negated_names.add(i["hpoName"])
        else:
            HPO_set.add(i["hpoId"])
            HPO_nset.add(i["hpoName"])
            HPO_results[i["hpoId"]]=i["hpoName"]
    # only use non-negated HPO IDs
    for i in HPO_set.difference(negated_HPOs):
        HPO_list.add(i)
    for i in HPO_nset.difference(negated_names):
        HPO_names.add(i)
    HPO_list, HPO_names = list(HPO_list), list(HPO_names)
    return HPO_list, HPO_names, HPO_results, res, doc2hpo_notes

def elasticquery(HPOquery,index,esettings="standard"):
    # default query
    query_json = \
    {'query': {
        "bool": {
            "should": [
                {
                "match": {
                    "NAME": {
                        "query": HPOquery,
                        "fuzziness": "AUTO:0,3",
                        "prefix_length" : 0,
                        "max_expansions": 50,
                        "boost": 1,
                        "operator": "or",
                        }
                    }
                },
                {
                "match": {
                    "NAME": {
                        "query": HPOquery,
                        "fuzziness": 0,
                        "boost": 2,
                    }
                    }
                },
                {
                "match_phrase": {
                    "NAMEEXACT": {
                        "query": HPOquery,
                        "boost": 3,
                    }
                    }
                },
        ]
        }
    },
        "sort": {"_score": {"order": "desc"}}
    }
    # if looking at linked terms only
    if esettings=="diseases":
        query_json = \
        {'query': {
            "bool": {
                "should": [
                    {
                    "match": {
                        "Linked HPO term": {
                            "query": HPOquery,
                            "fuzziness": 0,
                            "boost": 2,
                        }
                        }
                    },
            ]
            }
        },
            "sort": {"_score": {"order": "desc"}}
        }
    # if looking at linked terms + disease names
    if esettings=="hpolink":
        query_json = \
        {'query': {
            "bool": {
                "should": [
                    {
                    "match": {
                        "NAME": {
                            "query": HPOquery,
                            "fuzziness": "AUTO:0,3",
                            "prefix_length" : 0,
                            "max_expansions": 50,
                            "boost": 1,
                            "operator": "or",
                            }
                        }
                    },
                    {
                    "match": {
                        "Linked HPO term": {
                            "query": HPOquery,
                            "fuzziness": "AUTO:0,3",
                            "prefix_length" : 0,
                            "max_expansions": 50,
                            "boost": 1,
                            "operator": "or",
                            }
                        }
                    },
                    {
                    "match": {
                        "NAME": {
                            "query": HPOquery,
                            "fuzziness": 0,
                            "boost": 2,
                        }
                        }
                    },
                    {
                    "match": {
                        "Linked HPO term": {
                            "query": HPOquery,
                            "fuzziness": 0,
                            "boost": 3,
                        }
                        }
                    },
            ]
            }
        },
            "sort": {"_score": {"order": "desc"}}
        }

    result = {'result': indexquery(query_json,index=index,size=500)['hits']['hits']} # list of results line by line in "_source"

    return result
    

def results_page(HPOquery):

    # indices: doid, msh, icd10, irs990, open990f, open990g, umls, hpo, hpolink, ohdsi
    headers=generate_headers()
    hpo = elasticquery(HPOquery, 'hpo')
    hpo['header'] = headers['HPO']
    hpolink = elasticquery(HPOquery, 'hpolink', esettings="hpolink")
    if hpolink["result"]:
        diseases = defaultdict(dict)
        scores = defaultdict(float)
        for entry in hpolink["result"]:
            '''
entry = {'_index': 'hpolink', '_type': '_doc', '_id': '8dws1HQBR4YMZpofFYC7', '_score': 150.43999, '_source': {'Related Database ID': '260150', 'Database Name': 'OMIM', 'NAME': 'PALANT CLEFT PALATE SYNDROME', 'NAMEEXACT': 'PALANT CLEFT PALATE SYNDROME', 'Linked HPO ID': 'HP:0000175', 'Linked HPO term': 'Cleft palate'}}
            '''
            did = entry["_source"]["Related Database ID"]
            if scores[did] < entry["_score"]:
                diseases[did] = entry["_source"]
                diseases[did]["score"] = entry["_score"]
                scores[did] = entry["_score"]
    hpolink["result"] = diseases
    hpolink['header'] = headers['HPOlink']
    doid = elasticquery(HPOquery, 'doid')
    doid['header'] = headers['DO']
    msh = elasticquery(HPOquery, 'msh')
    msh['header'] = headers['MeSH']
    icd10 = elasticquery(HPOquery, 'icd10')
    icd10['header'] = headers['ICD-10']
    umls = elasticquery(HPOquery, 'umls')
    umls['header'] = headers['UMLS']
    ohdsi = elasticquery(HPOquery, 'ohdsi')
    ohdsi['header'] = headers['OHDSI']
    open990f = elasticquery(HPOquery, 'open990f')
    open990f['header'] = headers['990F']
    open990g = elasticquery(HPOquery, 'open990g')
    open990g['header'] = headers['990G']
    irs990 = elasticquery(HPOquery, 'irs990')
    irs990['header'] = headers['IRS']

    # for top HPO hit for Phen2Gene
    try:
        session['HPOID']=hpo['result'][0]['_source']['HPO ID']
    except IndexError:
        session['HPOID']=""

    # only allow internal redirect to results page
    # <wiki link> https://en.wikipedia.org/wiki/Waterhouse%E2%80%93Friderichsen_syndrome
    # <ICD-10 ID link> https://www.icd10data.com/search?s=A391&codebook=icd10all
    # <OMIM ID link> https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=248340
    # <HPO ID link> https://hpo.jax.org/app/browse/search?q=HP:0000377&navFilter=all
    # <HPO string> https://hpo.jax.org/app/browse/search?q=DiGeorge%20syndrome&navFilter=all

    cohd = {'result': API.generate_cohd_list(HPOquery)}
    cohd['header'] = headers['COHD']
    nihfoa = {'result': API.generate_nihfoa_list(HPOquery)}
    nihfoa['header'] = headers['NIHFOA']
    nihreporter = {'result': API.generate_nihreporter_list(HPOquery)}
    nihreporter['header'] = headers['NIHREPORT']
    phen2gene = {'result': API.phen2gene_page(session['HPOID'], patient=False)}
    phen2gene['header'] = headers['P2G']

    session['HPOquery'] = HPOquery.replace("_", "+").replace(" ","+")

    return doid, msh, icd10, irs990, open990f, open990g, umls, hpo, hpolink, ohdsi, phen2gene, cohd, nihfoa, nihreporter

def get_results_json():

    # get arguments from request
    HPO_list = request.args.get('HPO_list')

    if not HPO_list:  # no HPO IDs provided as argument to API
        results = "No HPO IDs provided"
    else:
        HPO_list = '10q22.3q23.3 microdeletion syndrome'
        results = json.loads(results_page(HPO_list))

    response = json.dumps({
        "results": results,
        "errors": errors
    }, default=set_default)

    return response

def hpo_from_phenopacket():
    # for serializing set to return as JSON
    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError
    # transform json format to dict
    data = json.loads(request.get_json(force=True))
    hpo_list = ''
    try:
        phenopacket = data['phenopacket']
    except KeyError:
        abort(400, '"phenopacket" not found!')
    try:
        phenotypes = phenopacket['phenotypic_features']
    except KeyError:
        try:
            phenotypes = phenopacket['phenotypicFeatures']
        except KeyError:
            abort(400, '"phenotypicFeatures" not found!')

    item_not_found = 0
    for item in phenotypes:
        try:
            hpo_id = item['type']['id']
            if (hpo_list == ''):
                hpo_list = hpo_id
            else:
                hpo_list += ';' + hpo_id
        except KeyError:
            item_not_found += 1
    if (len(hpo_list) <= 0):
        abort(400, 'No phenotypic features found!')

    results = get_results(hpo_list, weight_model='s')

    return results
