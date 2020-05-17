import json


def format_json_table(weight_model, gene_dict, type):
    gene_info_lst = []
    
    if len(gene_dict) > 0:

        # # when searching for ids
        # if weight_model == 'hpo':
        #     rank = 1
        #     for gene_item in gene_dict.keys():
        #         # phen_dict[idx].extend([phenName, HPOId, HPOName])
        #         gene_info_dict = {
        #             'HPO ID': gene_dict[gene_item][0],
        #             'HPO Name': gene_dict[gene_item][1],
        #             'Phenotype Name': gene_dict[gene_item][2],
        #         }
        #         gene_info_lst.append(gene_info_dict)
        #         rank += 1
        #
        # # when searching for terms instead of ids
        # else:
        if type == 'HPO':
            for gene_item in gene_dict.keys():
                # output_file.write(str(rank) + "\t" + gene_dict[gene_item][0] + "\t" + str(gene_item) + "\t" + str( np.round(gene_dict[gene_item][1] / highest_score, 6 ) ) + "\t" +gene_dict[gene_item][2] + "\n" )
                # phen_dict[idx].extend([phenName, HPOId, HPOName])
                gene_info_dict = {
                    'Phenotype Aliases': gene_dict[gene_item][0],
                    'HPO ID': gene_dict[gene_item][1],
                    'HPO Name': gene_dict[gene_item][2]
                }
                gene_info_lst.append(gene_info_dict)
        elif type == 'OMIM':
            for gene_item in gene_dict.keys():
                # phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
                gene_info_dict = {
                    'Disease Name': gene_dict[gene_item][0],
                    'OMIM ID': gene_dict[gene_item][1],
                    'Relative HPO ID': gene_dict[gene_item][2],
                    'HPO Name': gene_dict[gene_item][3]
                }
                gene_info_lst.append(gene_info_dict)
        elif type == 'DECIPHER':
            for gene_item in gene_dict.keys():
                # phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
                gene_info_dict = {
                    'Disease Name': gene_dict[gene_item][0],
                    'DECIPHER ID': gene_dict[gene_item][1],
                    'Relative HPO ID': gene_dict[gene_item][2],
                    'HPO Name': gene_dict[gene_item][3]
                }
                gene_info_lst.append(gene_info_dict)

        elif type == 'ORPHA':
            for gene_item in gene_dict.keys():
                # phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
                gene_info_dict = {
                    'Disease Name': gene_dict[gene_item][0],
                    'ORPHA ID': gene_dict[gene_item][1],
                    'Relative HPO ID': gene_dict[gene_item][2],
                    'HPO Name': gene_dict[gene_item][3]
                }
                gene_info_lst.append(gene_info_dict)
        elif type == 'ICD':
            for gene_item in gene_dict.keys():
                # phen_dict3[idx].extend([ICD10ID, PARENTIDX, ABBREV, NAME])
                gene_info_dict = {
                    'Phenotype Aliases': gene_dict[gene_item][3],
                    'ICD-10 ID': gene_dict[gene_item][0],
                    'Abbreviation Name': gene_dict[gene_item][2],
                    'Parent Index': gene_dict[gene_item][1]
                }
                gene_info_lst.append(gene_info_dict)
        elif type == 'UMLS':
            for gene_item in gene_dict.keys():
                # phen_dict_UMLS[idx].extend([CUI, LAT, LUI, CODE, STR])
                gene_info_dict = {
                    'Unique identifier for concept': gene_dict[gene_item][0],
                    'Language of term': gene_dict[gene_item][1],
                    'Unique identifier for term': gene_dict[gene_item][2],
                    'Most useful source asserted identifier': gene_dict[gene_item][3],
                    'Name string': gene_dict[gene_item][4]
                }
                gene_info_lst.append(gene_info_dict)

        elif type == 'SNOMED':
            for gene_item in gene_dict.keys():
                # phen_dict_SNOMED[idx].extend([conceptId, languageCode, term])
                gene_info_dict = {
                    'Concept Id': gene_dict[gene_item][0],
                    'Language Code': gene_dict[gene_item][1],
                    'Term': gene_dict[gene_item][2]
                }
                gene_info_lst.append(gene_info_dict)

    json_fmt = json.dumps(gene_info_lst)

    return json_fmt
