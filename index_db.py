from elasticsearch import Elasticsearch
from elasticsearch import helpers
import json
import time, datetime
import os
from datetime import datetime

time.sleep(30) # sleep until elastic is fully started.

es = Elasticsearch(['elasticsearch:9200'], timeout=60, retry_on_timeout=True)

def index_doid(INDEX_NAME='doid',path_to_txt='/media/database/DOID_data_result/DOID-DATA.txt'):
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": {
                    "type": "text"
                }
            }
        }
    }
    if es is not None:
            es.indices.delete(index=INDEX_NAME, ignore=404)
            es.indices.create(index=INDEX_NAME, body=request_body)
            es_data = []
            with open(path_to_txt, "r") as ftxt:
                a = ftxt.readlines()
                data = {}
                for i in a:
                    eles = i.split('\t')
                    data = {} # init to avoid deep copy.
                    data['ID'] = eles[0]
                    data['NAME'] = eles[1]
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 1000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)    

def index_msh(INDEX_NAME='msh',path_to_txt='/media/database/MSH_data_result/MSH-DATA.txt'):
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": {
                    "type": "text"
                }
            }
        }
    }
    if es is not None:
            es.indices.delete(index=INDEX_NAME, ignore=404)
            es.indices.create(index=INDEX_NAME, body=request_body)
            es_data = []
            with open(path_to_txt, "r") as ftxt:
                a = ftxt.readlines()
                data = {}
                for i in a:
                    eles = i.split('\t')
                    data = {} # init to avoid deep copy.
                    data['ID'] = eles[0]
                    data['NAME'] = eles[1]
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 1000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)

def index_icd10(INDEX_NAME='icd10',path_to_txt='/media/database/ICD10_data_result/ICD10-DATA.txt'):
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": {
                    "type": "text"
                },
                "ABBR": {
                    "type": "text"
                }
            }
        }
    }
    if es is not None:
            es.indices.delete(index=INDEX_NAME, ignore=404)
            es.indices.create(index=INDEX_NAME, body=request_body)
            es_data = []
            with open(path_to_txt, "r") as ftxt:
                a = ftxt.readlines()
                data = {}
                for i in a:
                    eles = i.split('\t')
                    data = {} # init to avoid deep copy.
                    data['ID'] = eles[1]
                    data['NAME'] = eles[4]
                    data['ABBR'] = eles[3]
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 1000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)        

def index_umls(INDEX_NAME='umls',path_to_txt='/media/database/UMLS-DATA.txt'):
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": {
                    "type": "text"
                }
            }
        }
    }
    if es is not None:
            es.indices.delete(index=INDEX_NAME, ignore=404)
            es.indices.create(index=INDEX_NAME, body=request_body)
            es_data = []
            with open(path_to_txt, "r") as ftxt:
                a = ftxt.readlines()
                data = {}
                for i in a:
                    eles = i.split('\t')
                    data = {} # init to avoid deep copy.
                    data['ID'] = eles[0]
                    data['NAME'] = eles[14] #IndexError: list index out of range
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 1000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)    

def index_autosuggest(INDEX_NAME='autosuggest',path_to_icd10='/media/database/ICD10_data_result/ICD10-DATA.txt',path_to_phenotype='/media/database/phenotype_database.csv'):
    request_body = {
        "settings": {
            "analysis": {
                "filter": {
                    "english_stop": {
                        "type": "stop",
                        "stopwords":  "_english_"
                        }
                },
                "analyzer": {
                    "rebuilt_stop": {
                    "tokenizer": "lowercase",
                    "filter": [
                        "english_stop","lowercase"          
                    ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": {
                    "type": "text",
                },
                "NAMESUGGEST":{ 
                    "type" : "completion",
                    "analyzer" : "rebuilt_stop"
                },
                "ABBR": {
                    "type": "text",
                }
            }
        }
    }
    
    if es is not None:
            es.indices.delete(index=INDEX_NAME, ignore=404)
            es.indices.create(index=INDEX_NAME, body=request_body)
            es_data = []
            n_doc = 0
            with open(path_to_icd10, "r") as ftxt:
                a = ftxt.readlines()
                data = {}
                for i in a:
                    eles = i.split('\t')
                    data = {} # init to avoid deep copy.
                    data['ID'] = eles[1]
                    data['NAME'] = eles[4]
                    data['ABBR'] = eles[3]
                    data['NAMESUGGEST'] = {}
                    data['NAMESUGGEST']['input'] = [eles[4]]
                    data['NAMESUGGEST']['input'].extend(eles[4].split())
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 10000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                        print("now =" + str(datetime.now()) + ': indexed ' + str(10000*n_doc) + ' documents')
                        n_doc += 1
                
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)   
                    print("now =" + str(datetime.now()) + ': indexed ICD10 is completed!')
                    
            es_data = []
            n_doc = 0
            with open(path_to_phenotype, "r") as ftxt:
                a = ftxt.readlines()
                data = {}
                for i in a:
                    eles = i.split('\t')
                    # Disease ID
                    data = {} # init to avoid deep copy.
                    data['ID'] = eles[2]
                    data['NAME'] = eles[1]
                    data['ABBR'] = ''
                    data['NAMESUGGEST'] = {}
                    data['NAMESUGGEST']['input'] = [eles[1]]
                    data['NAMESUGGEST']['input'].extend(eles[1].split())
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    # HPO ID
                    data = {} # init to avoid deep copy.
                    data['ID'] = eles[3]
                    data['NAME'] = eles[4]
                    data['ABBR'] = ''
                    data['NAMESUGGEST'] = {}
                    data['NAMESUGGEST']['input'] = [eles[1]]
                    data['NAMESUGGEST']['input'].extend(eles[1].split())
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 10000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                        print("now =" + str(datetime.now()) + ': indexed ' + str(10000*n_doc) + ' documents')
                        n_doc += 1

                
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)
                    print("now =" + str(datetime.now()) + ': indexed phenotype.db is completed!')
   


if __name__ == "__main__":
    # index_doid()
    # index_msh()
    # index_icd10()
    # index_umls() # TBD.
    index_autosuggest()



