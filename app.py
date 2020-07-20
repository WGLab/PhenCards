#!/usr/bin/env python

from collections import defaultdict
import sqlite3
from flask import Flask, Response, render_template, redirect, url_for, request, abort, flash, session, after_this_request, g, app
from forms import PhenCardsForm
from config import Config
from json2html import *
import sys
import json
import requests
from lib.json import format_json_table
import API
from flask_redis import FlaskRedis
import shutil
import tempfile
import weakref
import re
import os
from datetime import timedelta
import xml.etree.ElementTree as ET


# connect to SQLite at phenotype db file
conn = sqlite3.connect("/media/database/phenotype.db", check_same_thread=False)
# connect to PHENBASE
c1 = conn.cursor()
# connect to ICD10BASE
c2 = conn.cursor()

app = Flask(__name__)
# cors = CORS(app)
app.config.from_object(Config)
redis_client = FlaskRedis(app)

# results1 is used to store HPO related information, table 1 in result page
results1 = None
# results2 is used to store OMIM/DECIPHER/ORPHA information, table 2-4 in result page
results2OMIM = None
results2D = None
results2OR = None
# results3 is used to store ICD-10 information, table 5 in result page
results3 = None

# store UMLS and SNOMED database
resultsUMLS = None
resultsSNOMED = None

# use API from phen2gene web app
HPOID = 'cleft palate'

# errors and doc2hpo-error are for the errors storage
errors = None
doc2hpo_error = None

DOC2HPO_URL = "http://doc2hpo.wglab.org/parse/acdat" #"http://impact2.dbmi.columbia.edu/doc2hpo/parse/acdat" # can return to HTTPS when Columbia renews SSL cert and fixes site permanently
data = []

HPO_list = ''

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=24)

# get_results is for the SQL query functions
def get_results(phen_name: str, search_method='string', HPO_list=['cleft_palate']):
    global results1
    global results2OMIM
    global results2D
    global results2OR
    global results3
    global resultsUMLS
    global resultsSNOMED
    global HPOID
    global GeneAPI_JSON

    phen_name = phen_name.strip()
    # initialize values
    results1 = results2OMIM = results2D = results2OR = results3 = GeneAPI_JSON = None

    # (1) database id search
    if search_method == 'hpo':
        if not phen_name.isdigit():
            phen_name = '0'
        # use phen_dict as final result
        phen_dict1 = defaultdict(list)
        phen_dict2 = defaultdict(list)
        phen_dict2_OMIM = defaultdict(list)
        phen_dict2_DECIPHER = defaultdict(list)
        phen_dict2_ORPHA = defaultdict(list)
        phen_dict3 = defaultdict(list)
        cursor1 = c1.execute("SELECT * FROM PHENBASE WHERE [HPO-ID] LIKE'%" + phen_name + "%'")
        for row in cursor1:
            # index in database
            idx = row[0]
            phenName = row[1]
            OMIMID = row[2]
            HPOId = row[3]
            HPOName = row[4]
            phen_dict1[idx].extend([phenName, HPOId, HPOName])
            if OMIMID[:4] == 'OMIM':
                phen_dict2_OMIM[idx].extend([phenName, OMIMID, HPOId, HPOName])
            elif OMIMID[:8] == 'DECIPHER':
                phen_dict2_DECIPHER[idx].extend([phenName, OMIMID, HPOId, HPOName])
            elif OMIMID[:5] == 'ORPHA':
                phen_dict2_ORPHA[idx].extend([phenName, OMIMID, HPOId, HPOName])
            phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
        # print(phen_dict)
        cursor2 = c2.execute("SELECT * FROM ICD10BASE WHERE [ICD10-ID] LIKE'%" + phen_name + "%'")
        for row in cursor2:
            # index in database
            idx = row[0]
            ICD10ID = row[1]
            PARENTIDX = row[2]
            ABBREV = row[3]
            NAME = row[4]
            # output the JSON
            phen_dict3[idx].extend([ICD10ID, PARENTIDX, ABBREV, NAME])
        # output the JSON
        return format_json_table(phen_dict1, 'HPO'), format_json_table(phen_dict2_OMIM, 'OMIM'), \
               format_json_table(phen_dict2_DECIPHER, 'DECIPHER'), format_json_table(phen_dict2_ORPHA, 'ORPHA'), \
               format_json_table(phen_dict3, 'ICD'),

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
    cursor1 = c1.execute("SELECT * FROM PHENBASE WHERE DiseaseName LIKE'%" + phen_name + "%'") # where shawn searches DB, replace with elasticsearch
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
        phen_dict1[idx].extend([phenName, HPOId, HPOName])
        if OMIMID[:4] == 'OMIM':
            phen_dict2_OMIM[idx].extend([phenName, OMIMID, HPOId, HPOName])
        elif OMIMID[:8] == 'DECIPHER':
            phen_dict2_DECIPHER[idx].extend([phenName, OMIMID, HPOId, HPOName])
        elif OMIMID[:5] == 'ORPHA':
            phen_dict2_ORPHA[idx].extend([phenName, OMIMID, HPOId, HPOName])
        phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
        HPOID = phen_dict1[idx][1] # this is wrong.  this should not be here.
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


@app.route('/', methods=["GET", "POST"])
def phencards():
    global results1
    global results2OMIM
    global results2D
    global results2OR
    global results3
    global resultsUMLS
    global resultsSNOMED
    global doc2hpo_error
    global GeneAPI_JSON
    global HPO_list
    global HPO_names
    HPO_list = []
    HPO_names = []
    doc2hpo_error = None
    search_method = "string"
    phen_name = "cleft_palate" # default string
    # methods in form class
    form = PhenCardsForm()
    # validate_on_submit() method
    if form.validate_on_submit():
        doc2hpo_check = form.doc2hpo_check.data
        doc2hpo_notes = form.doc2hpo_notes.data

        # use doc2hpo to get HPO ids
        if doc2hpo_check:

            # default doc2hpo text
            if not doc2hpo_notes:
                doc2hpo_notes = "Individual II-1 is a 10 year old boy. He does not have synophrys. He was born at term with normal birth parameters and good APGAR scores (9/10/10). The neonatal period was uneventful, and he had normal motor development during early childhood: he began to look up at 3 months, sit by himself at 5 months, stand up at 11 months, walk at 13 months, and speak at 17 months. He attended a regular kindergarten, without any signs of difference in intelligence, compared to his peers. Starting at age 6, the parents observed ever increasing behavioral disturbance for the boy, manifesting in multiple aspects of life. For example, he can no longer wear clothes by himself, cannot obey instruction from parents/teachers, can no longer hold subjects tightly in hand, which were all things that he could do before 6 years of age. In addition, he no longer liked to play with others; instead, he just preferred to stay by himself, and he sometimes fell down when he walked on the stairs, which had rarely happened at age 5. The proband continued to deteriorate: at age 9, he could not say a single word and had no action or response to any instruction given in clinical exams. Additionally, rough facial features were noted with a flat nasal bridge, a synophrys (unibrow), a long and smooth philtrum, thick lips and an enlarged mouth. He also had rib edge eversion, and it was also discovered that he was profoundly deaf and had completely lost the ability to speak. He also had loss of bladder control. The diagnosis of severe intellectual disability was made, based on Wechsler Intelligence Scale examination. Brain MRI demonstrated cortical atrophy with enlargement of the subarachnoid spaces and ventricular dilatation (Figure 2). Brainstem evoked potentials showed moderate abnormalities. Electroencephalography (EEG) showed abnormal sleep EEG."

            # data to be sent to api 
            data = {
                "note": doc2hpo_notes,
                "negex": True  # default true for now
            }
            r = requests.post(url=DOC2HPO_URL, json=data)
            # r = requests.post(url = 'http://127.0.0.1:8000/doc2hpo/parse/acdat', json = data)

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
            # only use non-negated HPO IDs
            for i in HPO_set.difference(negated_HPOs):
                HPO_list.append(i)
            for i in HPO_nset.difference(negated_names):
                HPO_names.append(i)

        # get manually entered HPO IDs
        else:
            
            if form.phenname.data:
                phen_name = form.phenname.data

            # use autophenname in case there is an input.
            if form.typeahead.data:
                phen_name = form.typeahead.data
            # default HPO list

        results1, results2OMIM, results2D, results2OR, resultsUMLS, resultsSNOMED, results3 = get_results(phen_name, search_method, HPO_list)
        if doc2hpo_check: # runs doc2hpo instead of string match
            return redirect(url_for('patient_page'))
        HPO_list = [phen_name]
        return redirect(url_for('results_page'))
    return render_template('index.html', form=form)

@app.route('/patient')
def patient_page():
    global HPO_list
    phen_dict = defaultdict(list)
    HPOidstring=";".join(HPO_list)
    HPOquery="+OR+".join([s.replace(" ", "+") for s in HPO_names])
    print(HPOquery, file=sys.stderr)
    for i, (HPOId, HPOName) in enumerate(zip(HPO_list, HPO_names)):
        phen_dict[i].extend([HPOId, HPOName])
    results = format_json_table(phen_dict, 'patient')
    try:
        top_100 = json.loads(results)[:100]
    except:
        top_100 = results
    patient_table = json2html.convert(json=top_100,
                                    table_attributes="id=\"doc2hpo-results\" class=\"table table-striped table-bordered table-sm\"")
    try:
        GeneAPI_JSON = requests.get('https://phen2gene.wglab.org/api?HPO_list=' + HPOidstring + '&weight_model=sk', verify=False).json()['results'][:1000]
        phen2gene_table = json2html.convert(json=GeneAPI_JSON,
                                      table_attributes="id=\"phen2gene-api\" class=\"table table-striped table-bordered table-sm\"")
    except:
        phen2gene_table = ''

    session['HPOquery']=HPOquery
    return render_template('patient.html', patient_table=patient_table, phen2gene_table=phen2gene_table)
    

@app.route('/results')
def results_page():
    global HPO_list
    phenname = HPO_list[0]

    # if request.method == 'POST':
    #     return redirect(url_for('index'))

    # only allow internal redirect to results page
    # <wiki link> https://en.wikipedia.org/wiki/Waterhouse%E2%80%93Friderichsen_syndrome
    # <ICD-10 ID link> https://www.icd10data.com/search?s=A391&codebook=icd10all
    # <OMIM ID link> https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=248340
    # <HPO ID link> https://hpo.jax.org/app/browse/search?q=HP:0000377&navFilter=all
    # <HPO string> https://hpo.jax.org/app/browse/search?q=DiGeorge%20syndrome&navFilter=all
    def add_link_1(html_res):
        html_lst = html_res.split("</td>")
        for i in range(len(html_lst)):
            item = html_lst[i]

            if "<td>HP:" in item:
                # find index of the <td>
                idx = item.find("<td>HP:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(idx + 4):].replace(' ', '%20') \
                              + '&navFilter=all">' + item[(idx + 4):] + '</a>'
        html_res = '</td>'.join(html_lst)
        return html_res

    # <OMIM link> https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=DiGeorge+syndrome
    def add_link_2OMIM(html_res):
        html_lst = html_res.split("</td>")
        for i in range(len(html_lst)):
            item = html_lst[i]

            if "<td>HP:" in item:
                # find index of the <td>
                idx = item.find("<td>HP:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:( idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' + item[(idx + 4):].replace(' ', '+') \
                              + '>' + item[(idx + 4):] + '</a>'
        html_res = '</td>'.join(html_lst)
        return html_res

    def add_link_2D(html_res):
        html_lst = html_res.split("</td>")
        for i in range(len(html_lst)):
            item = html_lst[i]

            if "<td>HP:" in item:
                # find index of the <td>
                idx = item.find("<td>HP:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(idx + 4)] + '<a href=https://en.wikipedia.org/w/index.php?cirrusUserTesting=glent_m0&search=' + item[(idx + 4):].replace(' ', '%20') + '&title=Special%3ASearch&go=Go&ns0=1">' \
                              + item[(idx + 4):] + '</a>'
        html_res = '</td>'.join(html_lst)
        return html_res

    # https://bioportal.bioontology.org/search?q=DiGeorge%20Syndrome&ontologies=ORDO&include_properties=false&include_views=false&includeObsolete=false&require_definition=false&exact_match=false&categories=
    def add_link_2OR(html_res):
        html_lst = html_res.split("</td>")
        for i in range(len(html_lst)):
            item = html_lst[i]

            if "<td>HP:" in item:
                # find index of the <td>
                idx = item.find("<td>HP:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(idx + 4)] + '<a href=https://bioportal.bioontology.org/search?q=' + item[(idx + 4):].replace(' ', '%20') \
                              + '&ontologies=ORDO&include_properties=false&include_views=false&includeObsolete=false&require_definition=false&exact_match=false">' + item[(idx + 4):] + '</a>'
        html_res = '</td>'.join(html_lst)
        return html_res

    # <ICD link> https://www.icd10data.com/search?s=waterhouse-friderchsen%20syndrome&codebook=icd10all
    def add_link_3(html_res):
        html_lst = html_res.split("</td>")
        for i in range(len(html_lst)):
            item = html_lst[i]

            if "<td>HP:" in item:
                # find index of the <td>
                idx = item.find("<td>HP:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(
                                                                                                                       idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[(idx + 4):].replace(' ', '%20') \
                              + '&codebook=icd10all">' + item[(idx + 4):] + '</a>'
        html_res = '</td>'.join(html_lst)
        return html_res

    if not request.referrer:
        return redirect(url_for('phencards'))

    global errors

    # needs to be set to be rendered by HTML
    if not errors:
        errors = set()

    try:
        top_100_1 = json.loads(results1)[:100]
    except:
        top_100_1 = results1
    try:
        top_100_2OMIM = json.loads(results2OMIM)[:100]
    except:
        top_100_2OMIM = results2OMIM
    try:
        top_100_2D = json.loads(results2D)[:100]
    except:
        top_100_2D = results2D
    try:
        top_100_2OR = json.loads(results2OR)[:100]
    except:
        top_100_2OR = results2OR
    try:
        top_100_3 = json.loads(results3)[:100]
    except:
        top_100_3 = results3
    try:
        top_100_UMLS = json.loads(resultsUMLS)[:100]
    except:
        top_100_UMLS = resultsUMLS
    try:
        top_100_SNOMED = json.loads(resultsSNOMED)[:100]
    except:
        top_100_SNOMED = resultsSNOMED
    try:
        GeneAPI_JSON = requests.get('https://phen2gene.wglab.org/api?HPO_list=' + HPOID + '&weight_model=sk', verify=False).json()['results'][:100]
    except:
        pass
    try:
        GeneAPI_JSON = json.loads(GeneAPI_JSON)[:100]
    except:
        GeneAPI_JSON = GeneAPI_JSON

    html_table1 = json2html.convert(json=top_100_1,
                                    table_attributes="id=\"results-table1\" class=\"table table-striped table-bordered table-sm\"")
    html_table1 = add_link_1(html_table1)
    html_table2OMIM = json2html.convert(json=top_100_2OMIM,
                                        table_attributes="id=\"results-table2OMIM\" class=\"table table-striped table-bordered table-sm\"")
    html_table2OMIM = add_link_2OMIM(html_table2OMIM)
    html_table2D = json2html.convert(json=top_100_2D,
                                     table_attributes="id=\"results-table2D\" class=\"table table-striped table-bordered table-sm\"")
    html_table2D = add_link_2D(html_table2D)
    html_table2OR = json2html.convert(json=top_100_2OR,
                                      table_attributes="id=\"results-table2OR\" class=\"table table-striped table-bordered table-sm\"")
    html_table2OR = add_link_2OR(html_table2OR)
    html_table3 = json2html.convert(json=top_100_3,
                                    table_attributes="id=\"results-table3\" class=\"table table-striped table-bordered table-sm\"")
    html_table3 = add_link_3(html_table3)
    html_gene_api = json2html.convert(json=GeneAPI_JSON,
                                      table_attributes="id=\"results-gene-api\" class=\"table table-striped table-bordered table-sm\"")
    html_umls = json2html.convert(json=top_100_UMLS,
                                      table_attributes="id=\"results-umls\" class=\"table table-striped table-bordered table-sm\"")
    html_snomed = json2html.convert(json=top_100_SNOMED,
                                  table_attributes="id=\"results-snomed\" class=\"table table-striped table-bordered table-sm\"")

    API.api_reference(HPO_list[0])
    try:
        reference = API.api_reference(phenname).replace("\n",'<br>')
    except:
        reference = '<br>'

    session['HPOquery']=phenname.replace("_", "+").replace(" ","+")

    return render_template('results.html', html_table1=html_table1, html_table2OMIM=html_table2OMIM,
                           html_table2D=html_table2D, html_table2OR=html_table2OR, html_table3=html_table3,
                           html_umls=html_umls, html_gene_api=html_gene_api, html_snomed=html_snomed,
                           errors=errors, text1=reference)


# pathway results


@app.route('/pathway')
def generate_pathway_page():
    phenname=session['phenname']
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
        g.dispath = dispath

    return render_template('pathways.html', dispath=dispath)

# return independent page for drugs information

@app.route('/clinical')
def generate_clinical_page():
    HPOquery=session['HPOquery']
    try:
        clinicaljson = requests.get('https://clinicaltrials.gov/api/query/study_fields?expr='+ HPOquery +'&fields=NCTId%2CBriefTitle%2CCondition%2CInterventionName&min_rnk=1&max_rnk=1000&fmt=json', verify=False).json()['StudyFieldsResponse']
    except:
        clinicaljson = {}
    return render_template('clinical.html', clinicaljson=clinicaljson)

@app.route('/literature')
def generate_literature_page():
    pubmed={}
    HPOquery=session['HPOquery']
    rsearch=requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term="+HPOquery+"&retmax=5000&sort=relevance")
    root=ET.fromstring(rsearch.text)
    ids=[]
    for i in root.iter("Id"):
        ids.append(i.text)
    l=len(ids)
    for i in range(0,l,250):
        if l < i + 250:
            query=ids[i:l] 
        else:
            query=ids[i:i+250] 
        query=",".join(query)
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
            pubmed[id1]=publication
    return render_template('literature.html', pubmed=pubmed)

@app.route('/tocris')
def generate_tocris_page():
    HPOquery=session['HPOquery']
    drugs_lst = API.tocris_drugs_api(HPOquery)
    print(drugs_lst,file=sys.stderr)
    drugs = format_json_table(drugs_lst, 'DRUG')
    drugs = json2html.convert(json=drugs,
                              table_attributes="id=\"results-drugs\" class=\"table table-striped table-bordered table-sm\"",
                              escape=False)
    return render_template('tocris.html', tocris=drugs)

@app.route('/apexbio')
def generate_apexbio_page():
    HPOquery=session['HPOquery']
    drugs_lst = API.apexbt_drugs_api(HPOquery)
    print(drugs_lst,file=sys.stderr)
    return render_template('apexbio.html', apex=drugs_lst)


@app.route('/wikidata')
def generate_wikidata_page():
    link ="https://www.wikidata.org/w/index.php?search=drugs+for+" + "+".join(HPO_names)
    return redirect(link)


@app.route('/snomed')
def generate_snomed_page():
    return redirect("http://www.snomed.org/")


@app.route('/download_json/')
def download_json():
    return Response(results1, mimetype="application/json",
                    headers={"Content-disposition":
                                 "attachment; filename=results.json"})


# for serializing set to return as JSON
def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


# RESTful API
@app.route('/api', methods=["GET"])
def get_results_json():
    if request.method == 'GET':

        # get arguments from request
        HPO_list = request.args.get('HPO_list')
        weight_model = request.args.get('weight_model')

        if not HPO_list:  # no HPO IDs provided as argument to API
            results = "No HPO IDs provided"
        else:
            HPO_list = '10q22.3q23.3 microdeletion syndrome'
            results = json.loads(get_results(HPO_list, weight_model))

        response = json.dumps({
            "results": results,
            "errors": errors
        }, default=set_default)

        return Response(response, mimetype="application/json", status=200)


# Phenopacket
@app.route('/phenopacket', methods=["POST"])
def hpo_info_from_phenopacket():
    if request.method == 'POST':
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

        return Response(results, mimetype="application/json", status=200)

    else:
        abort(400, 'Bad request! Please use "POST" reuqest method!')


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.run(debug=True, port=5005)
    # print(res[0:10])
    # get_results('cleft')
