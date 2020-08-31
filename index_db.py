from elasticsearch import Elasticsearch
from elasticsearch import helpers
import json
import os
from datetime import datetime
from config import Config
from csv import DictReader as DR
from collections import defaultdict

es = Elasticsearch(["localhost:9200"], timeout=60, retry_on_timeout=True)
#es = Elasticsearch([Config.elasticsearch_url], timeout=60, retry_on_timeout=True)

def index_doid(INDEX_NAME='doid',path_to_doid='/media/database/DOID_data_result/DOID-DATA.txt'):
    request_body = {
        "settings": { 
            "index":{
                "max_ngram_diff": 20
                    },
    "analysis": {
      "analyzer": {
        "my_analyzer": {
          "type":"custom",
          "tokenizer": "my_tokenizer"
        }
      },
      "tokenizer": {
        "my_tokenizer": {
          "type": "ngram",
          "min_gram": 2 ,
          "max_gram": 10
        }
      }
    }},
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": { # Disease Name
                    "type": "text"
                },
                "NGRAM":{ 
                    "type" : "text",
                    "analyzer" : "my_analyzer"
                },
            }
        }
    }
    if es is not None:
            es.indices.delete(index=INDEX_NAME, ignore=404)
            es.indices.create(index=INDEX_NAME, body=request_body)
            es_data = []

            with open(path_to_doid, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                DOID-ID NAME
                """
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    data['ID'] = row['DOID-ID']
                    data['NAME'] = row['NAME']
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 1000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)    

def index_msh(INDEX_NAME='msh',path_to_mesh='/media/database/MSH_data_result/MSH-DATA.txt'):
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": { # msh term name/string
                    "type": "text"
                }
            }
        }
    }
    if es is not None:
            es.indices.delete(index=INDEX_NAME, ignore=404)
            es.indices.create(index=INDEX_NAME, body=request_body)
            es_data = []
            with open(path_to_mesh, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                DescriptorUI    DescriptorName
                """
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    data['ID'] = row['DescriptorUI']
                    data['NAME'] = row['DescriptorName']
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 1000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)

def index_icd10(INDEX_NAME='icd10',path_to_icd='/media/database/ICD10_data_result/ICD10-DATA.txt'):
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": { # disease name
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
            with open(path_to_icd, "r") as ftxt:
                data = {}
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                INDEX   ICD10-ID        PARENT-INDEX    ABBREV  NAME
                """
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    data['ID'] = row['ICD10-ID']
                    data['NAME'] = row['NAME']
                    data['ABBR'] = row['ABBREV']
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 1000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)        

def index_umls(INDEX_NAME='umls',path_to_umls='/media/database/UMLS-DATA.txt'):
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "ID": {
                    "type": "text"
                },
                "NAME": { # concept string umls
                    "type": "text"
                },
                "Source ID": {
                    "type": "text"
                },
                "Source Name": {
                    "type": "text"
                },
                "Source Type": {
                    "type": "text"
                },
                "Language": {
                    "type": "text"
                }
            }
        }
    }
    if es is not None:
            es.indices.delete(index=INDEX_NAME, ignore=404)
            es.indices.create(index=INDEX_NAME, body=request_body)
            es_data = []
            with open(path_to_umls, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                CUI     LAT     TS      LUI     STT     SUI     ISPREF  AUI     SAUI    SCUI    SDUI    SAB     TTY     CODE    STR     SRL     SUPPRESS        CVF
                """
                #2nd row is header description, but it is parseable, so...
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    data['ID'] = row['CUI']
                    data['NAME'] = row['STR']
                    data['Source ID'] = row['SDUI']
                    data['Source Name'] = row['SAB']
                    data['Source Type'] = row['TTY']
                    data['Language'] = row['LAT']
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 1000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)    

   

def index_irs990(INDEX_NAME='irs990',path_to_irs="/media/database/IRS990/index_2019.csv"): #update to 2020 in future, when updated
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "NAME": { # taxpaying foundation name
                    "type": "text"
                },
                "EIN": {
                    "type": "text"
                },
                "Date": {
                    "type": "text"
                },
                "ObjLink": {
                    "type": "text"
                }
            }
        }
    }
    if es is not None:
        es.indices.delete(index=INDEX_NAME, ignore=404)
        es.indices.create(index=INDEX_NAME, body=request_body)
        es_data = []
        with open(path_to_irs, "r") as ftxt:
            dictfile = DR(ftxt, dialect='excel')
            """
            RETURN_ID,FILING_TYPE,EIN,TAX_PERIOD,SUB_DATE,TAXPAYER_NAME,RETURN_TYPE,DLN,OBJECT_ID
            """
            for row in dictfile:
                data = {} # init to avoid deep copy.
                data['NAME'] = row['TAXPAYER_NAME']
                data['EIN'] = row['EIN']
                data['Date'] = row['SUB_DATE']
                data['ObjLink'] = row['OBJECT_ID'] # link = 'https://s3.amazonaws.com/irs-form-990/'+OBJECT_ID+'_public.xml'
                
                action = {"_index": INDEX_NAME, '_source': data}
                es_data.append(action)
                if len(es_data) > 1000:
                    helpers.bulk(es, es_data, stats_only=False)
                    es_data = []
            if len(es_data) > 0:
                helpers.bulk(es, es_data, stats_only=False)    

    return es_data

def index_open990(INDEX_NAME='open990f',INDEX_NAME2='open990g',path_to_foundations='/media/database/Open990/Open990_SnackSet_Foundations_Grants/Foundations.csv'
, path_to_grants="/media/database/Open990/Open990_SnackSet_Foundations_Grants/Grants.csv"):
    
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "NAME": { # Foundation Name
                    "type": "text"
                },
                "Address": {
                    "type": "text"
                },
                "Website": {
                    "type": "text"
                },
                "Email": {
                    "type": "text"
                },
                "Phone": {
                    "type": "text"
                },
                "EIN": {
                    "type": "text"
                }
            }
        }
    }

    if es is not None:
        es.indices.delete(index=INDEX_NAME, ignore=404)
        es.indices.create(index=INDEX_NAME, body=request_body)
        es_dataf, es_datag = [], []
        with open(path_to_foundations, "r") as ftxt:
            ftxt.readline() # noncommercial use only line. CC NC BY 4.0
            dictfile = DR(ftxt, dialect='excel')
            """
            EIN,Foundation name,Street,City,State,ZIP,Website,Email,Phone,NTEE code,NTEE description,Subsection,Deductible,Assets book value,Income,Exempt as of,Expenses,Contributions made,Contributions received,Activity 1,Activity 1 expense,Activity 2,Activity 2 expense,Activity 3,Activity 3 expense,Activity 4,Activity 4 expense,App preselect,App deadline,App restrictions,App form,App contact,App phone,App street,App city,App state,App ZIP,Grant maximum,Grant count,990-PF required,Tax period BMF,Tax period 990-PF
            """
            for row in dictfile:
                data = {} # init to avoid deep copy.
                data['NAME'] = row['Foundation name']
                data['Address'] = ",".join([row['Street'],row['City'],row['State'],row['ZIP']])
                data['Website'] = row['Website']
                data['Email'] = row['Email']
                data['Phone'] = row['Phone']
                data['EIN'] = row['EIN']
                
                action = {"_index": INDEX_NAME, '_source': data}
                es_dataf.append(action)
                if len(es_dataf) > 1000:
                    helpers.bulk(es, es_dataf, stats_only=False)
                    es_dataf = []
            if len(es_dataf) > 0:
                helpers.bulk(es, es_dataf, stats_only=False)    

    request_body2 = {
        "settings": {},
        "mappings": {
            "properties": {
                "NAME": { # Foundation name
                    "type": "text"
                },
                "Grantee": {
                    "type": "text"
                },
                "Grantee Location": {
                    "type": "text"
                },
                "Grant Purpose": {
                    "type": "text"
                },
                "Grant Amount": {
                    "type": "text"
                },
                "EIN": {
                    "type": "text"
                }
            }
        }
    }

    if es is not None:
        es.indices.delete(index=INDEX_NAME2, ignore=404)
        es.indices.create(index=INDEX_NAME2, body=request_body2)
        with open(path_to_grants, "r") as ftxt:
            ftxt.readline() # noncommercial use only line. CC NC BY 4.0
            dictfile = DR(ftxt, dialect='excel')
            """
            EIN,Foundation name,Grantee,City,State,Purpose,Amount,Paid,Future pay,Tax period 990-PF
            """
            for row in dictfile:
                data = {} # init to avoid deep copy.
                data['NAME'] = row['Foundation name']
                data['Grantee'] = row['Grantee']
                data['Grantee Location'] = ",".join([row['City'],row['State']])
                data['Grant Purpose'] = row['Purpose']
                data['Grant Amount'] = row['Amount']
                data['EIN'] = row['EIN']
                
                action = {"_index": INDEX_NAME2, '_source': data}
                es_datag.append(action)
                if len(es_datag) > 1000:
                    helpers.bulk(es, es_datag, stats_only=False)
                    es_datag = []
            if len(es_datag) > 0:
                helpers.bulk(es, es_datag, stats_only=False)    

    return es_dataf, es_datag

def index_ohdsi(INDEX_NAME='ohdsi',path_to_ohdsi="/media/database/OHDSI/CONCEPT.csv"): #update to 2020 in future, when updated
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "NAME": { # Concept Name
                    "type": "text"
                },
                "Concept ID": {
                    "type": "text"
                },
                "Domain": {
                    "type": "text"
                },
                "Vocabulary of Origin": {
                    "type": "text"
                },
                "Concept Class ID": {
                    "type": "text"
                },
                "Original Vocab ID": {
                    "type": "text"
                }
            }
        }
    }
    if es is not None:
        es.indices.delete(index=INDEX_NAME, ignore=404)
        es.indices.create(index=INDEX_NAME, body=request_body)
        es_data = []
        with open(path_to_ohdsi, "r") as ftxt:
            dictfile = DR(ftxt, dialect='excel-tab')
            """
            concept_id      concept_name    domain_id       vocabulary_id   concept_class_id        standard_concept        concept_code    valid_start_date        valid_end_date  invalid_reason
            """
            for row in dictfile:
                data = {} # init to avoid deep copy.
                data['NAME'] = row['concept_name']
                data['Concept ID'] = row['concept_id']
                data['Domain'] = row['domain_id']
                data['Vocabulary of Origin'] = row['vocabulary_id']
                data['Concept Class ID'] = row['concept_class_id']
                data['Original Vocab ID'] = row['concept_code']
                
                action = {"_index": INDEX_NAME, '_source': data}
                es_data.append(action)
                if len(es_data) > 1000:
                    helpers.bulk(es, es_data, stats_only=False)
                    es_data = []
            if len(es_data) > 0:
                helpers.bulk(es, es_data, stats_only=False)    

    return es_data

def index_hpo(INDEX_NAME='hpo',INDEX_NAME2='hpolink',path_to_hpo='/media/database/HPO/terms.tsv', path_to_phenotype='/media/database/HPO/phenotype_annotations.tsv'):
   # used https://github.com/macarthur-lab/obo_parser from MacArthur-Lab to format OBO file into terms.tsv, rest is in ipynb books
    request_body = {
        "settings": {},
        "mappings": {
            "properties": {
                "HPO ID": {
                    "type": "text"
                },
                "NAME": { # HPO term name/string
                    "type": "text"
                },
                "Alternate ID": {
                    "type": "text"
                },
                "Child IDs": {
                    "type": "text"
                },
                "Definition": {
                    "type": "text"
                },
                "Similar Subset Terms": {
                    "type": "text"
                },
                "External IDs": {
                    "type": "text"
                },
                "Parent IDs": {
                    "type": "text"
                }
            }
        }
    }

    if es is not None:
        es.indices.delete(index=INDEX_NAME, ignore=404)
        es.indices.create(index=INDEX_NAME, body=request_body)
        es_dataf, es_datag = [], []
        with open(path_to_hpo, "r") as ftxt:
            dictfile = DR(ftxt, dialect='excel-tab')
            """
            id      name    alt_id  children        comment created_by      creation_date   definition      parent_ids      subset  synonym xref
            """
            for row in dictfile:
                data = defaultdict(str) # init to avoid deep copy.
                data['HPO ID'] = row['id']
                data['NAME'] = row['name']
                data['Alternate ID'] = row['alt_id']
                data['Child IDs'] = row['children']
                data['Definition'] = row['definition']
                data['Parent IDs'] = row['parent_ids']
                data['Similar Subset Terms'] = row['subset']
                data['External IDs'] = row['xref']
                
                action = {"_index": INDEX_NAME, '_source': data}
                es_dataf.append(action)
                if len(es_dataf) > 1000:
                    helpers.bulk(es, es_dataf, stats_only=False)
                    es_dataf = []
            if len(es_dataf) > 0:
                helpers.bulk(es, es_dataf, stats_only=False)    

    request_body2 = {
        "settings": {},
        "mappings": {
            "properties": {
                "Related Database ID": {
                    "type": "text"
                },
                "Database Name": {
                    "type": "text"
                },
                "NAME": { # disease name
                    "type": "text"
                },
                "Linked HPO ID": {
                    "type": "text"
                },
                "Linked HPO term": {
                    "type": "text"
                }
            }
        }
    }

    if es is not None:
        es.indices.delete(index=INDEX_NAME2, ignore=404)
        es.indices.create(index=INDEX_NAME2, body=request_body2)
        with open(path_to_phenotype, "r") as ftxt:
            dictfile = DR(ftxt, dialect='excel-tab')
            """
            Index   DiseaseName     DatabaseID      HPO-ID  HPO-Name
            """
            for row in dictfile:
                data = {} # init to avoid deep copy.
                dbname, dbid = row['DatabaseID'].split(':')
                data['Related Database ID'] = dbid
                data['Database Name'] = dbname
                data['NAME'] = row['DiseaseName']
                data['Linked HPO ID'] = row['HPO-ID']
                data['Linked HPO term'] = row['HPO-Name']
                
                action = {"_index": INDEX_NAME2, '_source': data}
                es_datag.append(action)
                if len(es_datag) > 1000:
                    helpers.bulk(es, es_datag, stats_only=False)
                    es_datag = []
            if len(es_datag) > 0:
                helpers.bulk(es, es_datag, stats_only=False)    

    return es_dataf, es_datag

def index_autosuggest(INDEX_NAME='autosuggest', path_to_hpo='/media/database/HPO/terms.tsv', path_to_icd10='/media/database/ICD10_data_result/ICD10-DATA.txt', path_to_phenotype='/media/database/HPO/phenotype_annotations.tsv', path_to_ohdsi='/media/database/OHDSI/CONCEPT.csv', path_to_mesh='/media/database/MSH_data_result/MSH-DATA.txt', path_to_doid='/media/database/DOID_data_result/DOID-DATA.txt'):
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
                    "analyzer" : "rebuilt_stop",
                    "contexts" : [
                    {
                        "name": "set",
                        "type": "category"
                    },
                ]
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
            with open(path_to_hpo, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                id      name    alt_id  children        comment created_by      creation_date   definition      parent_ids      subset  synonym xref
                """
                for row in dictfile:
                    data = {}
                    data['ID'] = row['id']
                    data['NAME'] = row['name']
                    data['NAMESUGGEST'] = {}
                    data['NAMESUGGEST']['input'] = [row['name']]
                    data['NAMESUGGEST']['input'].extend(row['name'].split())
                    data['NAMESUGGEST']['contexts'] = {"set":['HPO']}
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 10000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                        print("now =" + str(datetime.now()) + ': indexed ' + str(10000*n_doc) + ' documents')
                        n_doc += 1
                
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)   
                    print("now =" + str(datetime.now()) + ': indexed HPO completed!')

            es_data = []
            n_doc = 0
            with open(path_to_icd10, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                INDEX   ICD10-ID        PARENT-INDEX    ABBREV  NAME
                """
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    data['ID'] = "ICD-10:"+row['ICD10-ID']
                    data['NAME'] = row['NAME']
                    data['NAMESUGGEST'] = {}
                    data['NAMESUGGEST']['input'] = [row['NAME']]
                    data['NAMESUGGEST']['input'].extend(row['NAME'].split())
                    data['NAMESUGGEST']['contexts'] = {"set":['ICD-10']}
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 10000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                        print("now =" + str(datetime.now()) + ': indexed ' + str(10000*n_doc) + ' documents')
                        n_doc += 1
                
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)   
                    print("now =" + str(datetime.now()) + ': indexed ICD10 completed!')
                    
            es_data = []
            n_doc = 0
            with open(path_to_phenotype, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                Index   DiseaseName     DatabaseID      HPO-ID  HPO-Name
                """
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    data['ID'] = row['DatabaseID']
                    data['NAME'] = row['DiseaseName']
                    data['NAMESUGGEST'] = {}
                    data['NAMESUGGEST']['input'] = [row['DiseaseName']]
                    data['NAMESUGGEST']['input'].extend(row['DiseaseName'].split())
                    data['NAMESUGGEST']['contexts'] = {"set":['HPOlink']}
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 10000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                        print("now =" + str(datetime.now()) + ': indexed ' + str(10000*n_doc) + ' documents')
                        n_doc += 1

                
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)
                    print("now =" + str(datetime.now()) + ': indexed HPO annotations completed!')
            
            es_data = []
            n_doc = 0
            with open(path_to_ohdsi, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                concept_id      concept_name    domain_id       vocabulary_id   concept_class_id        standard_concept        concept_code    valid_start_date        valid_end_date  invalid_reason
                """
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    if row ['domain_id'] == 'Condition':
                        data['ID'] = "OHDSI:"+row['concept_id']
                        data['NAME'] = row['concept_name']
                        data['NAMESUGGEST'] = {}
                        data['NAMESUGGEST']['input'] = [row['concept_name']]
                        data['NAMESUGGEST']['input'].extend(row['concept_name'].split())
                        data['NAMESUGGEST']['contexts'] = {"set":['OHDSI']}
                        action = {"_index": INDEX_NAME, '_source': data}
                        es_data.append(action)
                    if len(es_data) > 10000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                        print("now =" + str(datetime.now()) + ': indexed ' + str(10000*n_doc) + ' documents')
                        n_doc += 1

                
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)
                    print("now =" + str(datetime.now()) + ': indexed OHDSI completed!')

            es_data = []
            n_doc = 0
            with open(path_to_mesh, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                DescriptorUI    DescriptorName
                """
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    data['ID'] = "MeSH:"+row['DescriptorUI']
                    data['NAME'] = row['DescriptorName']
                    data['NAMESUGGEST'] = {}
                    data['NAMESUGGEST']['input'] = [row['DescriptorName']]
                    data['NAMESUGGEST']['input'].extend(row['DescriptorName'].split())
                    data['NAMESUGGEST']['contexts'] = {"set":['MeSH']}
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 10000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                        print("now =" + str(datetime.now()) + ': indexed ' + str(10000*n_doc) + ' documents')
                        n_doc += 1

                
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)
                    print("now =" + str(datetime.now()) + ': indexed MeSH completed!')

            es_data = []
            n_doc = 0
            with open(path_to_doid, "r") as ftxt:
                dictfile = DR(ftxt, dialect='excel-tab')
                """
                DOID-ID NAME
                """
                for row in dictfile:
                    data = {} # init to avoid deep copy.
                    data['ID'] = "DOID:"+row['DOID-ID']
                    data['NAME'] = row['NAME']
                    data['NAMESUGGEST'] = {}
                    data['NAMESUGGEST']['input'] = [row['NAME']]
                    data['NAMESUGGEST']['input'].extend(row['NAME'].split())
                    data['NAMESUGGEST']['contexts'] = {"set":['DOID']}
                    action = {"_index": INDEX_NAME, '_source': data}
                    es_data.append(action)
                    if len(es_data) > 10000:
                        helpers.bulk(es, es_data, stats_only=False)
                        es_data = []
                        print("now =" + str(datetime.now()) + ': indexed ' + str(10000*n_doc) + ' documents')
                        n_doc += 1

                
                if len(es_data) > 0:
                    helpers.bulk(es, es_data, stats_only=False)
                    print("now =" + str(datetime.now()) + ': indexed DOID completed!')

if __name__ == "__main__":
    index_open990()
    index_irs990()
    index_doid()
    index_msh()
    index_icd10()
    index_umls()
    index_ohdsi()
    index_hpo()
    index_autosuggest()
