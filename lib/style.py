from config import Config
from csv import DictReader as DR
from collections import defaultdict

def generate_headers():
    headers=defaultdict(list)
    with open(Config.path_to_headers,"r") as csvfile:
        dictfile = DR(csvfile, dialect='excel-tab')
        for row in dictfile:
            headers[row['db']].append({'term': row['term'], 'definition': row['definition']})
    return headers
