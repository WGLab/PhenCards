from lib.json import format_json_table
from config import Config
import sqlite3
from flask import session, request
from collections import defaultdict
from json2html import json2html
import API

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

def results_page(phenname, HPOquery):
    # get_results is for the SQL query functions
    c1, c2 = connect_to_db(Config.path_to_phenotypedb)
    results1, results2OMIM, results2D, results2OR, resultsUMLS, resultsSNOMED, results3 = get_results(phenname, c1, c2)
    print (results1)

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
    html_umls = json2html.convert(json=top_100_UMLS,
                                      table_attributes="id=\"results-umls\" class=\"table table-striped table-bordered table-sm\"")
    html_snomed = json2html.convert(json=top_100_SNOMED,
                                  table_attributes="id=\"results-snomed\" class=\"table table-striped table-bordered table-sm\"")
    cohd = API.generate_cohd_list(HPOquery)
    phen2gene=API.phen2gene_page(session['HPOID'], patient=False)

    session['HPOquery']=phenname.replace("_", "+").replace(" ","+")

    return html_table1, html_table2OMIM, html_table2D, html_table2OR, html_table3, html_umls, phen2gene, html_snomed, cohd
