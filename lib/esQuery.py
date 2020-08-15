from elasticsearch import Elasticsearch
from typing import List
from flask import Markup
from config import Config

def indexquery(query_json,index='autosuggest', size=10):
    '''
    backend implementation of esquery for autosuggest
    query_json: elastic search json.
    '''
    es = Elasticsearch([Config.elasticsearch_url], timeout=60, retry_on_timeout=True)
    query_string_query = query_json
    result = es.search(index=index, body=query_string_query,size=size)
    return result


