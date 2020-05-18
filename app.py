#!/usr/bin/env python

from collections import defaultdict
import sqlite3
from flask import Flask, Response, render_template, redirect, url_for, request, abort, flash
from forms import Phen2GeneForm
from config import Config
from json2html import *
import json
import requests
from lib.json import format_json_table
import API

# connect to SQLite at phenotype db file
conn = sqlite3.connect("/database/phenotype.db", check_same_thread=False)
# connect to PHENBASE
c1 = conn.cursor()
# connect to ICD10BASE
c2 = conn.cursor()

app = Flask(__name__)
# cors = CORS(app)
app.config.from_object(Config)

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

DOC2HPO_URL = "https://impact2.dbmi.columbia.edu/doc2hpo/parse/acdat"
data = []

HPO_list = ''


# get_results is for the SQL query functions
def get_results(phen_name: str, weight_model='pn'):
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

    # (1) if search by hpo id
    if weight_model == 'hpo':
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
        return format_json_table(weight_model.lower(), phen_dict1, 'HPO'), format_json_table(weight_model.lower(),
                                                                                             phen_dict2_OMIM, 'OMIM'), \
               format_json_table(weight_model.lower(), phen_dict2_DECIPHER, 'DECIPHER'), format_json_table(
            weight_model.lower(), phen_dict2_ORPHA, 'ORPHA'), \
               format_json_table(weight_model.lower(), phen_dict3, 'ICD'),

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
    cursor1 = c1.execute("SELECT * FROM PHENBASE WHERE DiseaseName LIKE'%" + phen_name + "%'")
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
        HPOID = phen_dict1[idx][1]
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
    return format_json_table(weight_model.lower(), phen_dict1, 'HPO'), \
           format_json_table(weight_model.lower(), phen_dict2_OMIM, 'OMIM'), \
           format_json_table(weight_model.lower(), phen_dict2_DECIPHER, 'DECIPHER'),\
           format_json_table(weight_model.lower(), phen_dict2_ORPHA, 'ORPHA'), \
           format_json_table(weight_model.lower(), phen_dict_UMLS, 'UMLS'), \
           format_json_table(weight_model.lower(), phen_dict_SNOMED, 'SNOMED'), \
           format_json_table(weight_model.lower(), phen_dict3, 'ICD')


@app.route('/', methods=["GET", "POST"])
def phen2Gene():
    global results1
    global results2OMIM
    global results2D
    global results2OR
    global results3
    global resultsUMLS
    global resultsSNOMED
    global doc2hpo_error
    global GeneAPI_JSON
    doc2hpo_error = None

    # methods in form class
    form = Phen2GeneForm()
    # validate_on_submit() method
    if form.validate_on_submit():
        weight_model = form.weight_model.data
        doc2hpo_check = form.doc2hpo_check.data
        doc2hpo_notes = form.doc2hpo_notes.data

        # use doc2hpo to get HPO ids
        if doc2hpo_check:

            # default doc2hpo text
            if not doc2hpo_notes:
                doc2hpo_notes = ""

            # data to be sent to api 
            data = {
                "note": doc2hpo_notes,
                "negex": True  # default true for now
            }

            r = requests.post(url=DOC2HPO_URL, json=data)
            # r = requests.post(url = 'http://127.0.0.1:8000/doc2hpo/parse/acdat', json = data)

            # check if doc2hpo request is successful
            # if status code of response starts with 2, it is successful, otherwise something is wrong with doc2hpo

            if int(str(r.status_code)[:1]) != 2:
                r = requests.post(url='http://127.0.0.1:8000/doc2hpo/parse/acdat', json=data)
                if int(str(r.status_code)[:1]) != 2:
                    doc2hpo_error = "Doc2Hpo service is temporarily unavailable and cannot process clinical notes. Please manually input HPO terms instead."
                    flash(doc2hpo_error)
                    return redirect(url_for('phen2Gene'))

            res = r.json()
            res = res["hmName2Id"]

            HPO_set = set()
            negated_HPOs = set()

            for i in res:
                if i["negated"]:
                    negated_HPOs.add(i["hpoId"])
                else:
                    HPO_set.add(i["hpoId"])
            global HPO_list
            HPO_list = ""
            # only use non-negated HPO IDs
            for i in HPO_set.difference(negated_HPOs):
                HPO_list += i + ";"
            # remove last semicolon
            HPO_list = HPO_list[:-1]

        # get manually entered HPO IDs
        else:
            HPO_list = form.HPO_list.data
            # default HPO list
            if not HPO_list:
                HPO_list = "cleft palate"

        results1, results2OMIM, results2D, results2OR, resultsUMLS, resultsSNOMED, results3 = get_results(HPO_list, weight_model)
        return redirect(url_for('results_page'))
    return render_template('index.html', form=form)


@app.route('/results')
def results_page():
    global HPO_list

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
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(
                                                                                                                       idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(
                            idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(
                                                                                                                       idx + 4):].replace(
                    ' ', '%20') \
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
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(
                                                                                                                       idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(
                            idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(
                            idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' + item[
                                                                                                                                                          (
                                                                                                                                                                      idx + 4):].replace(
                    ' ', '+') \
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
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(
                                                                                                                       idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(
                            idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(
                            idx + 4)] + '<a href=https://en.wikipedia.org/w/index.php?cirrusUserTesting=glent_m0&search=' + item[
                                                                                                                            (
                                                                                                                                        idx + 4):].replace(
                    ' ', '%20') \
                              + '&title=Special%3ASearch&go=Go&ns0=1">' + item[(idx + 4):] + '</a>'
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
                html_lst[i] = item[:(idx + 4)] + '<a href=https://hpo.jax.org/app/browse/search?q=' + item[(
                                                                                                                       idx + 4):] + "&navFilter=all>" \
                              + item[(idx + 4):] + '</a>'

            elif "<td>OMIM:" in item:
                idx = item.find("<td>OMIM:")
                html_lst[i] = item[:(
                            idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(idx + 4)] + '<a href=https://bioportal.bioontology.org/search?q=' + item[(
                                                                                                                          idx + 4):].replace(
                    ' ', '%20') \
                              + '&ontologies=ORDO&include_properties=false&include_views=false&includeObsolete=false&require_definition=false&exact_match=false">' + item[
                                                                                                                                                                     (
                                                                                                                                                                                 idx + 4):] + '</a>'
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
                html_lst[i] = item[:(
                            idx + 4)] + '<a href=https://www.omim.org/search/?index=entry&start=1&limit=10&sort=score+desc%2C+prefix_sort+desc&search=' \
                              + item[(idx + 9):] + ">" + item[(idx + 4):] + '</a>'

            elif "<td>" in item:
                idx = item.find("<td>")
                if item[idx + 4] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and item[idx + 5:].isdigit():
                    html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[idx + 4:] \
                                  + "&codebook=icd10all>" + item[(idx + 4):] + '</a>'
                    continue
                html_lst[i] = item[:(idx + 4)] + '<a href=https://www.icd10data.com/search?s=' + item[
                                                                                                 (idx + 4):].replace(
                    ' ', '%20') \
                              + '&codebook=icd10all">' + item[(idx + 4):] + '</a>'
        html_res = '</td>'.join(html_lst)
        return html_res

    if not request.referrer:
        return redirect(url_for('phen2Gene'))

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
    GeneAPI_JSON = \
    requests.get('https://phen2gene.wglab.org/api?HPO_list=' + HPOID + '&weight_model=sk', verify=False).json()[
        'results'][:100]
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
    reference = API.kegg_api_reference(HPO_list).replace('\n', '<br>')
    drugs = API.apexbt_drugs_api(HPO_list).replace('\n', '<br>')
    return render_template('results.html', html_table1=html_table1, html_table2OMIM=html_table2OMIM,
                           html_table2D=html_table2D, html_table2OR=html_table2OR, html_table3=html_table3,
                           html_umls=html_umls, html_gene_api=html_gene_api, html_snomed=html_snomed,
                           errors=errors, text1=reference, text2=drugs)


# page for API documentation
@app.route('/docs')
def instructions_page():
    return render_template('instructions.html')


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
    app.run()
    # print(res[0:10])
    # get_results('cleft')
