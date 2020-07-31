#!/usr/bin/env python

from flask import Flask, Response, render_template, redirect, url_for, request, abort, flash, session, app
import sys
import requests
from datetime import timedelta
import API
import queries
from forms import PhenCardsForm
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=24)

@app.route('/', methods=["GET", "POST"])
def phencards():
    HPO_list = []
    HPO_names = []
    doc2hpo_error = None
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
            DOC2HPO_URL = "http://doc2hpo.wglab.org/parse/acdat" #"http://impact2.dbmi.columbia.edu/doc2hpo/parse/acdat" # can return to HTTPS when Columbia renews SSL cert and fixes site permanently
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

        if doc2hpo_check: # runs doc2hpo instead of string match
            session['HPOquery']=HPO_list
            session['HPOnames']=HPO_names
            return redirect(url_for('generate_patient_page'))
        HPO_list = [phen_name]
        session['HPOquery']=phen_name
        return redirect(url_for('generate_results_page'))
    return render_template('index.html', form=form)

@app.route('/patient')
def generate_patient_page():
    HPOquery = session['HPOquery']
    HPO_names = session['HPOnames']
    session['HPOclinical'], patient_table, phen2gene_table = API.patient_page(HPOquery, HPO_names)
    print(HPOquery, file=sys.stderr)
    return render_template('patient.html', patient_table=patient_table, phen2gene_table=phen2gene_table)

@app.route('/results')
def generate_results_page():
    phenname=session['HPOquery']
    HPOquery=session['HPOquery']
    html_table1, html_table2OMIM, html_table2D, html_table2OR, html_table3, html_umls, phen2gene, html_snomed, cohd = queries.results_page(phenname, HPOquery)
    return render_template('results.html', html_table1=html_table1, html_table2OMIM=html_table2OMIM,
                           html_table2D=html_table2D, html_table2OR=html_table2OR, html_table3=html_table3,
                           html_umls=html_umls, phen2gene=phen2gene, html_snomed=html_snomed, cohd=cohd)

# pathway results
@app.route('/pathway')
def generate_pathway_page():
    phenname=session['HPOquery']
    dispath=API.pathway_page(phenname)
    return render_template('pathways.html', dispath=dispath)

# cohd results
@app.route('/cohd')
def generate_cohd_page():
    concept_id=request.args.get('concept')
    ancestors, conditions, drugs, procedures = API.cohd_page(concept_id)
    return render_template('cohd.html', conditions=conditions,drugs=drugs,procedures=procedures,ancestors=ancestors)

# clinical trials results
@app.route('/clinical')
def generate_clinical_page():
    HPOquery=session['HPOquery']
    if 'HPOclinical' in session:
        clinicaljson=API.clinical_page(session['HPOclinical'])
    else:
        clinicaljson=API.clinical_page(HPOquery)
    return render_template('clinical.html', clinicaljson=clinicaljson)

# literature (pubmed) results
@app.route('/literature')
def generate_literature_page():
    HPOquery=session['HPOquery']
    pubmed=API.literature_page(HPOquery)
    return render_template('literature.html',pubmed=pubmed)

# return independent page for tocris drugs information
@app.route('/tocris')
def generate_tocris_page():
    HPOquery=session['HPOquery']
    tocris=API.tocris_drugs_api(HPOquery)
    return render_template('tocris.html', tocris=tocris)

# return independent page for apexbio drugs information
@app.route('/apexbio')
def generate_apexbio_page():
    HPOquery=session['HPOquery']
    apex=API.apexbt_drugs_api(HPOquery)
    return render_template('apexbio.html', apex=apex)

# return independent page for wikidata drugs information (not done yet)
@app.route('/wikidata')
def generate_wikidata_page():
    link ="https://www.wikidata.org/w/index.php?search=drugs+for+" + "+".join(session['HPOquery'])
    return redirect(link)

@app.route('/download_json/')
def download_json():
    return Response(results1, mimetype="application/json", # will need to add link to HPO results later
                    headers={"Content-disposition":
                                 "attachment; filename=results.json"})

# RESTful API
@app.route('/api', methods=["GET"])
def apiroute():
    response = queries.get_results_json()  
    return Response(response, mimetype="application/json", status=200)

# Phenopackets
@app.route('/phenopacket', methods=["POST"])
def phenopacket():
    results = queries.hpo_from_phenopacket() 
    return Response(results, mimetype="application/json", status=200)


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    # app.run(host="0.0.0.0", debug=True)
    app.run(debug=True, port=5005)
