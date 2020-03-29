#!/usr/bin/env python

from collections import defaultdict
import sqlite3
from flask import Flask, Response, render_template, redirect, url_for, request, abort, flash
from flask_cors import CORS
from forms import Phen2GeneForm
from config import Config
from json2html import *
import json
import requests
from lib.json import format_json_table

# connect to SQLite at phenotype db file
conn = sqlite3.connect("./database/phenotype.db", check_same_thread=False)
# connect to PHENBASE
c1 = conn.cursor()
# connect to ICD10BASE
c2 = conn.cursor()

app = Flask(__name__)
cors = CORS(app)
app.config.from_object(Config)

# results1 is used to store HPO related information, table 1 in result page
results1 = None
# results2 is used to store OMIM/DECIPHER/ORPHA information, table 2-4 in result page
results2OMIM = None
results2D = None
results2OR = None
# results3 is used to store ICD-10 information, table 5 in result page
results3 = None

# errors and doc2hpo-error are for the errors storage
errors = None
doc2hpo_error = None

DOC2HPO_URL = "https://impact2.dbmi.columbia.edu/doc2hpo/parse/acdat"
data = []


# get_results is for the SQL query functions
def get_results(phen_name: str, weight_model='pn'):
    global results1
    global results2OMIM
    global results2D
    global results2OR
    global results3

    phen_name = phen_name.strip()
    # initialize values
    results1 = results2OMIM = results2D = results2OR = results3 = None

    # (1) if search by hpo id
    if weight_model == 'hpo':
        if phen_name == None:
            return "No input detected."
        # use phen_dict as final result
        phen_dict1 = defaultdict(list)
        phen_dict2 = defaultdict(list)
        cursor1 = c1.execute("SELECT * FROM PHENBASE WHERE [HPO-ID]='" + phen_name + "'")
        for row in cursor1:
            # index in database
            idx = row[0]
            phenName = row[1]
            OMIMID = row[2]
            HPOId = row[3]
            HPOName = row[4]
            phen_dict1[idx].extend([HPOId, HPOName, phenName, OMIMID])
            phen_dict2[idx].extend([phenName, OMIMID])
        # print(phen_dict)

        # output the JSON
        return format_json_table(weight_model.lower(), phen_dict1, 'HPO'), format_json_table(weight_model.lower(),
                                                                                             phen_dict1, 'OMIM')

    # If no phenotype name available, exit the scripts.
    if phen_name is None:
        return "No input detected."

    # (2) when searching by string:

    phen_dict1 = defaultdict(list)
    phen_dict2 = defaultdict(list)
    phen_dict2_OMIM = defaultdict(list)
    phen_dict2_DECIPHER = defaultdict(list)
    phen_dict2_ORPHA = defaultdict(list)
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
        phen_dict3[idx].extend([ICD10ID, PARENTIDX, ABBREV, NAME])

    # return results in json file, transfer dict into json format
    return format_json_table(weight_model.lower(), phen_dict1, 'HPO'), format_json_table(weight_model.lower(),
                                                                                         phen_dict2_OMIM, 'OMIM'), \
           format_json_table(weight_model.lower(), phen_dict2_DECIPHER, 'DECIPHER'), format_json_table(
        weight_model.lower(), phen_dict2_ORPHA, 'ORPHA'), \
           format_json_table(weight_model.lower(), phen_dict3, 'ICD')


@app.route('/', methods=["GET", "POST"])
def phen2Gene():
    global results1
    global results2OMIM
    global results2D
    global results2OR
    global results3
    global doc2hpo_error
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
                HPO_list = "SYNDROME"

        results1, results2OMIM, results2D, results2OR, results3 = get_results(HPO_list, weight_model)
        return redirect(url_for('results_page'))
    return render_template('index.html', form=form)


@app.route('/results')
def results_page():
    # only allow internal redirect to results page
    if not request.referrer:
        return redirect(url_for('phen2Gene'))

    global errors

    # needs to be set to be rendered by HTML
    if not errors:
        errors = set()

    try:
        top_1000_1 = json.loads(results1)[:1000]
    except:
        top_1000_1 = results1
    try:
        top_1000_2OMIM = json.loads(results2OMIM)[:1000]
    except:
        top_1000_2OMIM = results2OMIM
    try:
        top_1000_2D = json.loads(results2D)[:1000]
    except:
        top_1000_2D = results2D
    try:
        top_1000_2OR = json.loads(results2OR)[:1000]
    except:
        top_1000_2OR = results2OR
    try:
        top_1000_3 = json.loads(results3)[:1000]
    except:
        top_1000_3 = results3

    html_table1 = json2html.convert(json=top_1000_1,
                                    table_attributes="id=\"results-table1\" class=\"table table-striped table-bordered table-sm\"")
    html_table2OMIM = json2html.convert(json=top_1000_2OMIM,
                                        table_attributes="id=\"results-table2OMIM\" class=\"table table-striped table-bordered table-sm\"")
    html_table2D = json2html.convert(json=top_1000_2D,
                                     table_attributes="id=\"results-table2D\" class=\"table table-striped table-bordered table-sm\"")
    html_table2OR = json2html.convert(json=top_1000_2OR,
                                      table_attributes="id=\"results-table2OR\" class=\"table table-striped table-bordered table-sm\"")
    html_table3 = json2html.convert(json=top_1000_3,
                                    table_attributes="id=\"results-table3\" class=\"table table-striped table-bordered table-sm\"")

    return render_template('results.html', html_table1=html_table1, html_table2OMIM=html_table2OMIM,
                           html_table2D=html_table2D, html_table2OR=html_table2OR, html_table3=html_table3,
                           errors=errors)


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
    # get_results('a')
