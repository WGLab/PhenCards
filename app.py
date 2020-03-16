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

knowledgebase = "./lib/Knowledgebase/"

conn = sqlite3.connect("./database/phenotype.db", check_same_thread=False)
c1 = conn.cursor()
c2 = conn.cursor()

app = Flask(__name__)
cors = CORS(app)
app.config.from_object(Config)

results = None
errors = None
doc2hpo_error = None

DOC2HPO_URL = "https://impact2.dbmi.columbia.edu/doc2hpo/parse/acdat"
data = []
# //////////////////////////////////////// start


def get_results(phen_name: str, weight_model='pn'):
    global results
    phen_name = phen_name.strip()
    results = None

    # if search by hpo id
    if weight_model == 'hpo':
        if phen_name == None:
            return "No input detected."
        # use phen_dict as final result
        phen_dict = defaultdict(list)
        cursor1 = c1.execute("SELECT * FROM PHENBASE WHERE [HPO-ID]='" + phen_name + "'")
        for row in cursor1:
            # index in database
            idx = row[0]
            phenName = row[1]
            exDb = row[2]
            HPOId = row[3]
            HPOName = row[4]
            phen_dict[idx].extend([HPOId, HPOName, phenName, exDb])
        # print(phen_dict)

        # output the JSON
        return format_json_table(weight_model.lower(), phen_dict)

    # If no phenotype name available, exit the scripts.
    if phen_name == None:
        return "No input detected."

    phen_dict = defaultdict(list)
    cursor1 = c1.execute("SELECT * FROM PHENBASE WHERE DiseaseName LIKE'%" + phen_name + "%'")
    for row in cursor1:
        # index in database
        idx = row[0]
        phenName = row[1]
        exDb = row[2]
        HPOId = row[3]
        HPOName = row[4]
        # print(HPOId)
        '''
        if HPOId not in HPOSet:
            HPOSet.add(HPOId)
            cursor2 = c2.execute("SELECT * FROM EXTERNALBASE WHERE [HPO-ID]='" + HPOId + "'")
            for item in cursor2:
                refDb = item[1] + ': ' + item[2]
                refName = item[3]
        '''
        phen_dict[idx].extend([phenName, exDb, HPOId, HPOName])
    # print(phen_dict)

    # output the JSON
    return format_json_table(weight_model.lower(), phen_dict)


@app.route('/', methods=["GET", "POST"])
def phen2Gene():
    global results
    global doc2hpo_error
    doc2hpo_error = None
    # * methods in form class?
    form = Phen2GeneForm()
    # * validate_on_submit() method?
    if form.validate_on_submit():
        weight_model = form.weight_model.data
        doc2hpo_check = form.doc2hpo_check.data
        doc2hpo_notes = form.doc2hpo_notes.data

        # use doc2hpo to get HPO ids
        if doc2hpo_check:

            # default doc2hpo text
            if not doc2hpo_notes:
                doc2hpo_notes = "He denies synophrys. Individual II-1 is a 10 year old boy. He was born at term with normal birth parameters and good APGAR scores (9/10/10). The neonatal period was uneventful, and he had normal motor development during early childhood: he began to look up at 3 months, sit by himself at 5 months, stand up at 11 months, walk at 13 months, and speak at 17 months. He attended a regular kindergarten, without any signs of difference in intelligence, compared to his peers. Starting at age 6, the parents observed ever increasing behavioral disturbance for the boy, manifesting in multiple aspects of life. For example, he can no longer wear clothes by himself, cannot obey instruction from parents/teachers, can no longer hold subjects tightly in hand, which were all things that he could do before 6 years of age. In addition, he no longer liked to play with others; instead, he just preferred to stay by himself, and he sometimes fell down when he walked on the stairs, which had rarely happened at age 5. The proband continued to deteriorate: at age 9, he could not say a single word and had no action or response to any instruction given in clinical exams. Additionally, rough facial features were noted with a flat nasal bridge, a synophrys (unibrow), a long and smooth philtrum, thick lips and an enlarged mouth. He also had rib edge eversion, and it was also discovered that he was profoundly deaf and had completely lost the ability to speak. He also had loss of bladder control. The diagnosis of severe intellectual disability was made, based on Wechsler Intelligence Scale examination. Brain MRI demonstrated cortical atrophy with enlargement of the subarachnoid spaces and ventricular dilatation (Figure 2). Brainstem evoked potentials showed moderate abnormalities. Electroencephalography (EEG) showed abnormal sleep EEG.";

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
                HPO_list = "JOUBERT SYNDROME 30; JBTS30"

        results = get_results(HPO_list, weight_model)
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
        top_1000 = json.loads(results)[:1000]
    except:
        top_1000 = results

    html_table = json2html.convert(json=top_1000,
                                   table_attributes="id=\"results-table\" class=\"table table-striped table-bordered table-sm\"")
    return render_template('results.html', html_table=html_table, errors=errors)


# page for API documentation
@app.route('/docs')
def instructions_page():
    return render_template('instructions.html')


@app.route('/download_json/')
def download_json():
    return Response(results, mimetype="application/json",
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
    # res = get_results("HP:0000707;HP:0007598;HP:0001156;HP:0012446", weight_model = 'u')
    # print(res[0:10])
    # get_results('10q22.3q23.3 microdeletion syndrome')