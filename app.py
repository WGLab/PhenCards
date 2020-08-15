#!/usr/bin/env python

from flask import Flask, Response, render_template, redirect, url_for, request, jsonify, abort, flash, session, app
import sys
from datetime import timedelta
import API
import queries
from forms import PhenCardsForm
from config import Config
from lib.esQuery import indexquery

app = Flask(__name__)
app.config.from_object(Config)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=24)

@app.route('/', methods=["GET", "POST"])
def phencards():
    phen_name = "cleft palate" # default string
    # methods in form class
    form = PhenCardsForm()
    # validate_on_submit() method
    if form.validate_on_submit():
        doc2hpo_check = form.doc2hpo_check.data
        doc2hpo_notes = form.doc2hpo_notes.data

        # use doc2hpo to get HPO ids
        if doc2hpo_check: # runs doc2hpo instead of string match
            HPO_list, HPO_names = queries.doc2hpo(doc2hpo_notes)
            session['HPOquery']=HPO_list
            session['HPOnames']=HPO_names
            return redirect(url_for('generate_patient_page'))

        # get manually entered HPO IDs
        else:
            
            if form.phenname.data:
                phen_name = form.phenname.data

            # use autophenname in case there is an input.
            if form.typeahead.data:
                phen_name = form.typeahead.data

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
    #phenname=session['HPOquery']
    HPOquery=session['HPOquery']
    #html_table1, html_table2OMIM, html_table2D, html_table2OR, html_table3, html_umls, phen2gene, html_snomed, cohd = queries.results_page(phenname, HPOquery)
    doid, msh, icd10, irs990, open990f, open990g, umls, hpo, hpolink, ohdsi, phen2gene, cohd = queries.results_page(HPOquery)
    return render_template('results.html', doid=doid, msh=msh, icd10=icd10, irs990=irs990, open990f=open990f, open990g=open990g, umls=umls, hpo=hpo, hpolink=hpolink, ohdsi=ohdsi, phen2gene=phen2gene, cohd=cohd)
    #return render_template('results.html', html_table1=html_table1, html_table2OMIM=html_table2OMIM,
    #                       html_table2D=html_table2D, html_table2OR=html_table2OR, html_table3=html_table3,
    #                       html_umls=html_umls, phen2gene=phen2gene, html_snomed=html_snomed, cohd=cohd)

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

# autosuggest
@app.route('/autosuggest', methods=['POST'])
def get_autosuggest():
    query_json = request.json
    results = indexquery(query_json, index = 'autosuggest')
    return jsonify(results)



if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    # app.run(host="0.0.0.0", debug=True)
    # binding to 0.0.0.0 if you want the container to be accessible from outside.
    app.run(host="0.0.0.0",debug=True, port=5002)
