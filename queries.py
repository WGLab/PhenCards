from lib.json import format_json_table
from config import Config
import sqlite3
from flask import session
from collections import defaultdict

def connect_to_db(path_to_db):

    # connect to SQLite at phenotype db file
    conn = sqlite3.connect(path_to_db, check_same_thread=False)
    # connect to PHENBASE
    c1 = conn.cursor()
    # connect to ICD10BASE
    c2 = conn.cursor()

    return c1, c2

HPOquery="cleft palate"

def get_results(phen_name: str, phencurs, icdcurs):

    c1, c2 = phencurs, icdcurs

    phen_name = phen_name.strip()
    # initialize values
    results1 = results2OMIM = results2D = results2OR = results3 = None


    # If no phenotype name available, exit the scripts.
    if phen_name is None:
        return "No input detected."

    # (2) when searching by string:

    phen_dict1 = defaultdict(list)
    phen_dict2 = defaultdict(list)
    phen_dict2_OMIM = defaultdict(list)
    phen_dict2_DECIPHER = defaultdict(list)
    phen_dict2_ORPHA = defaultdict(list)
    phen_dict_UMLS = defaultdict(list)
    phen_dict_SNOMED = defaultdict(list)
    phen_dict3 = defaultdict(list)

    # use c1 to get data from PHENBASE
    #cursor1 = c1.execute("SELECT * FROM PHENBASE WHERE DiseaseName LIKE'%" + phen_name + "%'") # where shawn searches DB, replace with elasticsearch
    phen_like="%".join(phen_name.split())
    cursor1 = c1.execute("select * from PHENBASE where \"HPO-Name\" like '%" + phen_like + "%' order by \"HPO-Name\" = \"" + phen_name + "\";") # if searching by ID, use "HPO-ID" or similar
    ct=1
    # parse data in cursor1 through analyzing each item in SQL return tuple
    for row in cursor1:
        # index in database
        idx = row[0]
        phenName = row[1]
        OMIMID = row[2]
        HPOId = row[3]
        HPOName = row[4]

        # the following code was supposed to be used for searching related information in EXTERNALBASE
        '''
        if HPOId not in HPOSet:
            HPOSet.add(HPOId)
            cursor2 = c2.execute("SELECT * FROM EXTERNALBASE WHERE [HPO-ID]='" + HPOId + "'")
            for item in cursor2:
                refDb = item[1] + ': ' + item[2]
                refName = item[3]
        '''

        # add dictionaries for the result page
        phen_dict1[HPOId]=[HPOId, HPOName]
        if OMIMID[:4] == 'OMIM':
            phen_dict2_OMIM[idx].extend([phenName, OMIMID, HPOId, HPOName])
        elif OMIMID[:8] == 'DECIPHER':
            phen_dict2_DECIPHER[idx].extend([phenName, OMIMID, HPOId, HPOName])
        elif OMIMID[:5] == 'ORPHA':
            phen_dict2_ORPHA[idx].extend([phenName, OMIMID, HPOId, HPOName])
        phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
        if ct == 1:
            session['HPOID']=HPOId
            ct+=1
    # use c2 to get information inside ICD10BASE
    cursor2 = c2.execute("SELECT * FROM ICD10BASE WHERE NAME LIKE'%" + phen_name + "%'")
    for row in cursor2:
        # index in database
        idx = row[0]
        ICD10ID = row[1]
        PARENTIDX = row[2]
        ABBREV = row[3]
        NAME = row[4]
        # output the JSON
        # if NAME.lower().startswith(phen_name.lower()):
        phen_dict3[idx].extend([ICD10ID, PARENTIDX, ABBREV, NAME])

    cursor2 = c2.execute("SELECT CUI, LAT, LUI, CODE, STR FROM UMLSBASE WHERE STR LIKE'%" + phen_name + "%'")
    idx = 0
    for row in cursor2:
        # index in database
        idx += 1
        CUI = row[0]
        LAT = row[1]
        LUI = row[2]
        CODE = row[3]
        STR = row[4]
        # output the JSON
        # if NAME.lower().startswith(phen_name.lower()):
        phen_dict_UMLS[idx].extend([CUI, LAT, LUI, CODE, STR])

    cursor2 = c2.execute("SELECT id, conceptId, languageCode, term FROM SNOMEDBASE WHERE term LIKE'%" + phen_name + "%'")
    for row in cursor2:
        # index in database
        idx = row[0]
        conceptId = row[1]
        languageCode = row[2]
        term = row[3]
        # output the JSON
        # if NAME.lower().startswith(phen_name.lower()):
        phen_dict_SNOMED[idx].extend([conceptId, languageCode, term])

    # return results in json file, transfer dict into json format
    return format_json_table(phen_dict1, 'HPO'), \
           format_json_table(phen_dict2_OMIM, 'OMIM'), \
           format_json_table(phen_dict2_DECIPHER, 'DECIPHER'),\
           format_json_table(phen_dict2_ORPHA, 'ORPHA'), \
           format_json_table(phen_dict_UMLS, 'UMLS'), \
           format_json_table(phen_dict_SNOMED, 'SNOMED'), \
           format_json_table(phen_dict3, 'ICD')

#results1, results2OMIM, results2D, results2OR, resultsUMLS, resultsSNOMED, results3 = get_results(phen_name, c1, c2)

