#!/usr/bin/env python

from flask import Flask, Response, render_template, redirect, url_for, request, jsonify, abort, flash, session, app, send_from_directory
from sqlalchemy import create_engine, Column, Text, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
import sys
from datetime import timedelta
import API
import queries
from forms import PhenCardsForm
from config import Config
from lib.esQuery import indexquery
from lib.style import generate_headers
import os

app = Flask(__name__)
app.config.from_object(Config)

db_name=Config.db_name
SQLALCHEMY_DATABASE_URL = 'sqlite:///' + db_name
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
db = SessionLocal()

class Query(Base):
    __tablename__ = 'Queries'
    term = Column(Text, unique=True, primary_key=True, nullable=False)
    cnt = Column(Integer, default=0)
    def __repr__(self):
        return '<Query %r: %d>' % (self.term, self.cnt)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/ico'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=8)

@app.route('/', methods=["GET", "POST"])
def phencards():
    phen_name = "craniosynostosis" # default string, make sure to always test with cleft palate or similar, for whitespace interpretation is different on different APIs
    # methods in form class
    form = PhenCardsForm()
    # validate_on_submit() method
    if form.validate_on_submit():
        doc2hpo_check = form.doc2hpo_check.data
        doc2hpo_notes = form.doc2hpo_notes.data

        # use doc2hpo to get HPO ids
        if doc2hpo_check: # runs doc2hpo instead of string match
            HPO_list, HPO_names, HPO_results, res, note = queries.doc2hpo(doc2hpo_notes)
            session['HPOquery']=HPO_list
            session['HPOnames']=HPO_names
            session['HPOresults']=HPO_results
            session['parsingJson'] = res
            session['doc2hpo_notes'] = note
            return redirect(url_for('generate_patient_page'))

        # get manually entered HPO IDs
        else:
            
            # use autocomplete.
            if form.typeahead.data:
                phen_name = form.typeahead.data

        session['HPOquery']=session['HPOclinical']=phen_name
        ## STORE THE QUERIES HERE IN SQL DB, LOWERCASE
        Base.metadata.create_all(bind=engine)
        q = session['HPOquery'].lower()
        Q = Query(term=q)
        try:
            j = len(db.query(Query).filter_by(term=q).all())
            if j == 0:
                print ("new entry")
                db.add(Q)
            else:
                db.query(Query).filter_by(term=q).update({Query.cnt: Query.cnt + 1})
            db.commit()
        except IntegrityError as e:
            db.rollback()
            print ("rollback", e)
        print (db.query(Query).filter_by(term=q).all())
        return redirect(url_for('generate_results_page'))
    term = request.args.get('term')
    if term:
        session['HPOquery']=session['HPOclinical']=term
        return redirect(url_for('generate_results_page'))
    return render_template('index.html', form=form)

@app.route('/patient')
def generate_patient_page():
    HPOquery = session['HPOquery']
    HPOnames = sorted(session['HPOnames'])
    HPOresults = session['HPOresults']
    d2hjson = session['parsingJson']
    doc2hpo_notes = session['doc2hpo_notes']
    session['HPOclinical'], phen2gene, headers, linked_diseases = API.patient_page(HPOquery, HPOnames, d2hjson)
    print(HPOquery, file=sys.stderr)
    return render_template('patient.html', phen2gene=phen2gene, HPOnames=HPOnames, HPOresults=HPOresults, d2hjson=d2hjson, headers=headers, linked_diseases=linked_diseases, note=doc2hpo_notes)

@app.route('/results')
def generate_results_page():
    global umls
    HPOquery=session['HPOquery']
    doid, msh, icd10, irs990, open990f, open990g, umls, hpo, hpolink, ohdsi, phen2gene, pharos, cohd, nihfoa, nihreporter = queries.results_page(HPOquery)
    return render_template('results.html', doid=doid, msh=msh, icd10=icd10, irs990=irs990, open990f=open990f, open990g=open990g, hpo=hpo, hpolink=hpolink, ohdsi=ohdsi, phen2gene=phen2gene, pharos=pharos, cohd=cohd, nihfoa=nihfoa, nihreporter=nihreporter)

@app.route('/umls')
def generate_umls_page():
    ticket = request.args['ticket']
    valid = API.umls_auth(ticket)
    print (valid, file=sys.stderr)
    if valid:
        return render_template('umls.html', umls=umls)
    else:
        flash('Invalid credentials')
        return redirect(url_for('generate_results_page'))

# pharos results
@app.route('/pharos')
def generate_pharos_page():
    HPOquery=session['HPOquery']
    facetdata, headers = API.pharos_page(HPOquery)
    return render_template('pharos.html', facetdata=facetdata, headers=headers)

@app.route('/pharostarget')
def generate_pharos_target_page():
    target=request.args.get('target')
    details, expressions, ligands, ppis, headers = API.pharos_target_details(target)
    return render_template('pharostarget.html', target=target, details=details, expressions=expressions, ligands=ligands, ppis=ppis, headers=headers)

# kegg pathway results
@app.route('/kegg')
def generate_kegg_page():
    HPOquery=session['HPOquery']
    dispath, headers = API.kegg_page(HPOquery)
    return render_template('kegg.html', dispath=dispath, headers=headers)

# pathway commons results
@app.route('/pcommons')
def generate_pcommons_page():
    HPOquery=session['HPOquery']
    pathways, headers = API.pcommons_page(HPOquery)
    return render_template('pcommons.html', pathways=pathways, headers=headers)

# cohd results
@app.route('/cohd')
def generate_cohd_page():
    concept_id=request.args.get('concept')
    ancestors, conditions, drugs, procedures, headers = API.cohd_page(concept_id)
    return render_template('cohd.html', conditions=conditions, drugs=drugs, procedures=procedures, ancestors=ancestors, headers=headers)

# clinical trials results
@app.route('/clinical')
def generate_clinical_page():
    if 'HPOclinical' in session:
        clinicaljson, headers = API.clinical_page(session['HPOclinical'])
    else:
        clinicaljson={}
    return render_template('clinical.html', clinicaljson=clinicaljson, headers=headers)

# literature (pubmed) results
@app.route('/literature')
def generate_literature_page():
    HPOquery=session['HPOquery']
    pubmed, headers = API.literature_page(HPOquery)
    return render_template('literature.html',pubmed=pubmed, headers=headers)

@app.route('/protocol')
def generate_protocol_page():
    HPOquery=session['HPOquery']
    proto, headers = API.protocol_page(HPOquery)
    return render_template('protocol.html', proto=proto, headers=headers)

# return independent page for tocris drugs information
@app.route('/tocris')
def generate_tocris_page():
    HPOquery=session['HPOquery']
    tocris, headers = API.tocris_drugs_api(HPOquery)
    return render_template('tocris.html', tocris=tocris, headers=headers)

# return independent page for apexbio drugs information
@app.route('/apexbio')
def generate_apexbio_page():
    HPOquery=session['HPOquery']
    apex, headers = API.apexbt_drugs_api(HPOquery)
    return render_template('apexbio.html', apex=apex, headers=headers)

# return independent page for wikidata drugs information (not done yet)
@app.route('/openfda')
def generate_openfda_page():
    HPOquery=session['HPOquery']
    synonyms, drugs, forms, weights, outcomes, ages, routes, drugi, reactioni, routei, headers = API.openfda_page(HPOquery) 
    return render_template('openfda.html', synonyms=synonyms, drugs=drugs, forms=forms, weights=weights, outcomes=outcomes, ages=ages, routes=routes, drugi=drugi, reactioni=reactioni, routei=routei, headers=headers)

@app.route('/download_json/')
def download_json():
    return Response(results1, mimetype="application/json", # will need to add link to HPO results later
                    headers={"Content-disposition":
                                 "attachment; filename=results.json"})
@app.route('/tutorial')
def generate_tutorial_page():
    return render_template('tutorial.html')

# RESTful API
@app.route('/d2e', methods=["GET"])
def generate_d2e():
    HPOquery = request.args.get('query')
    print(HPOquery, file=sys.stderr)
    d2e = API.direct2experts(HPOquery)
    return d2e

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

@app.route('/api/v1/resources/drugcentral/query', methods=['GET'])
def api_drugcentral_drugs():
    HPOquery = request.args.get('query')
    version, dfs = API.DrugCentral(HPOquery)
    return jsonify(version, dfs)

@app.route('/api/v1/resources/drugcentral/ddi', methods=['GET'])
def api_drugcentral_ddi():
    drugname = request.args.get('name')
    ddis = API.getDrugDDIs(drugname)
    return jsonify(ddis)

@app.route('/api/v1/resources/headers', methods=['GET'])
def api_headers():
    #table = request.args.get('table')
    headers = generate_headers()
    #headers = headers[table]
    return jsonify(headers)

if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    # app.run(host="0.0.0.0", debug=True)
    # binding to 0.0.0.0 if you want the container to be accessible from outside.
    app.run(host="0.0.0.0",debug=True, port=5005)
