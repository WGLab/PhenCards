import numpy as np 
import json


def format_json(weight_model, gene_dict):
    
    gene_info_lst = []

    if(len(gene_dict) > 0):

        if(weight_model == 's'):

            gene_ID = list(gene_dict.keys())
            begin = 0
            score = gene_dict[gene_ID[0]][1]
            highest_score  = score
            cnt = 0
            for i in range(len(gene_ID)):
                if(gene_dict[gene_ID[i]][1] == score):
                    cnt += 1
                else:
                    rank_ave =  int(begin + 1 + cnt /2)
                    for j in range(begin, i):
                        gene_info_dict = {}
                        gene_info_dict[gene_dict[gene_ID[j]][0]] = {'Rank':str(rank_ave) , 'gene_id':str(gene_ID[j]),'score':str( float(gene_dict[gene_ID[j]][1]/highest_score)), 'status': gene_dict[gene_ID[j]][2] }
                        gene_info_lst.append(gene_info_dict)
                        #output_file.write(str(rank_ave) + "\t" + gene_dict[gene_ID[j]][0] + "\t" + str(gene_ID[j]) + "\t" + str( float(gene_dict[gene_ID[j]][1]/highest_score)  ) + "\t" + gene_dict[gene_ID[j]][2] + "\n" )


                    score = gene_dict[gene_ID[i]][1]
                    begin = i
                    cnt = 0

            if(begin < len(gene_ID)):
                rank_ave =  int( (begin + len(gene_ID)) /2)
                for j in range(begin, len(gene_ID)):
                    gene_info_dict = {}
                    gene_info_dict[gene_dict[gene_ID[j]][0]] = {'Rank':str(rank_ave) , 'gene_id':str(gene_ID[j]),'score':str( float(gene_dict[gene_ID[j]][1]/highest_score)), 'status':gene_dict[gene_ID[j]][2]}
                    gene_info_lst.append(gene_info_dict)
                    #output_file.write(str(rank_ave) + "\t" + gene_dict[gene_ID[j]][0] + "\t" + str(gene_ID[j]) + "\t" + str( gene_dict[gene_ID[j]][1]  ) + "\t" + gene_dict[gene_ID[j]][2] + "\n" )

        else:
            rank = 1
            highest_score = 1
            for gene_item in gene_dict.keys():
                if(rank == 1):
                    highest_score = gene_dict[gene_item][1]
                #output_file.write(str(rank) + "\t" + gene_dict[gene_item][0] + "\t" + str(gene_item) + "\t" + str( np.round(gene_dict[gene_item][1] / highest_score, 6 ) ) + "\t" +gene_dict[gene_item][2] + "\n" )
                gene_info_dict = {}
                gene_info_dict[gene_dict[gene_item][0]] = {'Rank':str(rank) , 'gene_id':str(gene_item),'score':str(np.round(gene_dict[gene_item][1] / highest_score, 6 ) ), 'status':gene_dict[gene_item][2]}
                gene_info_lst.append(gene_info_dict)
                rank += 1
                                    
    json_fmt = json.dumps(gene_info_lst)
    return json_fmt


def format_json_table(weight_model, gene_dict, type):
    gene_info_lst = []
    
    if(len(gene_dict) > 0):

        if(weight_model == 'hpo'):
            rank = 1
            for gene_item in gene_dict.keys():
                # phen_dict[idx].extend([phenName, HPOId, HPOName])
                gene_info_dict = {
                    'HPO ID': gene_dict[gene_item][0],
                    'HPO Name': gene_dict[gene_item][1],
                    'Phenotype Name': gene_dict[gene_item][2],
                }
                gene_info_lst.append(gene_info_dict)
                rank += 1

        else:
            if type == 'HPO':
                for gene_item in gene_dict.keys():
                    # output_file.write(str(rank) + "\t" + gene_dict[gene_item][0] + "\t" + str(gene_item) + "\t" + str( np.round(gene_dict[gene_item][1] / highest_score, 6 ) ) + "\t" +gene_dict[gene_item][2] + "\n" )
                    # phen_dict[idx].extend([phenName, HPOId, HPOName])
                    gene_info_dict = {
                        'Phenotype Name': gene_dict[gene_item][0],
                        'HPO ID': gene_dict[gene_item][1],
                        'HPO Name': gene_dict[gene_item][2]
                    }
                    gene_info_lst.append(gene_info_dict)
            elif type == 'OMIM':
                for gene_item in gene_dict.keys():
                    # phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
                    gene_info_dict = {
                        'Phenotype Name': gene_dict[gene_item][0],
                        'OMIM ID': gene_dict[gene_item][1],
                        'HPO ID': gene_dict[gene_item][2],
                        'HPO Name': gene_dict[gene_item][3]
                    }
                    gene_info_lst.append(gene_info_dict)
            elif type == 'DECIPHER':
                for gene_item in gene_dict.keys():
                    # phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
                    gene_info_dict = {
                        'Phenotype Name': gene_dict[gene_item][0],
                        'DECIPHER ID': gene_dict[gene_item][1],
                        'HPO ID': gene_dict[gene_item][2],
                        'HPO Name': gene_dict[gene_item][3]
                    }
                    gene_info_lst.append(gene_info_dict)

            elif type == 'ORPHA':
                for gene_item in gene_dict.keys():
                    # phen_dict2[idx].extend([phenName, OMIMID, HPOId, HPOName])
                    gene_info_dict = {
                        'Phenotype Name': gene_dict[gene_item][0],
                        'ORPHA ID': gene_dict[gene_item][1],
                        'HPO ID': gene_dict[gene_item][2],
                        'HPO Name': gene_dict[gene_item][3]
                    }
                    gene_info_lst.append(gene_info_dict)
            elif type == 'ICD':
                for gene_item in gene_dict.keys():
                    # phen_dict3[idx].extend([ICD10ID, PARENTIDX, ABBREV, NAME])
                    gene_info_dict = {
                        'ICD-10 Name': gene_dict[gene_item][3],
                        'ICD-10 ID': gene_dict[gene_item][0],
                        'Abbreviation Name': gene_dict[gene_item][2],
                        'Parent Index': gene_dict[gene_item][1]
                    }
                    gene_info_lst.append(gene_info_dict)
                                    
    json_fmt = json.dumps(gene_info_lst)
    return json_fmt