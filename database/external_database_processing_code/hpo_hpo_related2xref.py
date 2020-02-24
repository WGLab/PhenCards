import networkx as nx 
import re 
import matplotlib as plt

valid_hpo_id_cnt = 0

hpo_dg = nx.DiGraph()

def clean_term_data(HPid,xref,is_a,name,definition,is_obsolete,replaced_by,consider,alt_id,synonym,created_by, creation_date,comment, subset,property_value):
    HPid = ""
    xref = []
    synonym = []
    is_a = []
    name = ""

    definition = ""
    is_obsolete = False
    replaced_by = []
    consider = []
    alt_id = []

    created_by = ""
    creation_date = ""
    comment = ""
    subset = ""
    property_value = ""

    return (HPid,xref,is_a,name,definition,is_obsolete,replaced_by,consider,alt_id,synonym,created_by, creation_date,comment,subset,property_value)


cnt_term = 0
with open("./hpo.obo", "r") as fr:

    HPid = ""
    name = ""
    synonym = []
    xref = []
    is_a = []
    
    definition = ""
    is_obsolete = False
    replaced_by = []
    consider = []
    alt_id = []

    created_by = ""
    creation_date = ""
    comment = ""
    subset = ""
    property_value = ""

    new_term = "[Term]"

    hpo_headers = True

    for line in fr:
        if(line.startswith(new_term)):
            cnt_term += 1
            if(hpo_headers == True):
                hpo_headers = False
                (HPid,xref,is_a,name,definition,is_obsolete,replaced_by,consider,alt_id,synonym,created_by, creation_date,comment,subset,property_value) = clean_term_data(HPid,xref,is_a,name,definition,is_obsolete,
                            replaced_by,consider,alt_id,synonym,created_by, creation_date,comment,subset,property_value)
                continue

            #update nodes
            node_updates = [(HPid, {'name':name, 'is_a':is_a, 'definition':definition, 'xref':xref, 'syn':synonym, 
                            'is_obsolete':is_obsolete, 'replaced_by':replaced_by,'consider':consider, 'alt_id':alt_id,
                            'created_by':created_by,'creation_date':creation_date, 'comment':comment, 'subset':subset})]
            #update edges
            edges_updates = []
            for parent in is_a:
                edges_updates.append((HPid, parent))

            if(not is_obsolete):
                hpo_dg.update(edges = edges_updates, nodes = node_updates)
            else:
                hpo_dg.update(nodes=node_updates)

            (HPid,xref,is_a,name,definition,is_obsolete,replaced_by,consider,alt_id,synonym,created_by, creation_date,comment,subset,property_value) = clean_term_data(HPid,xref,is_a,name,definition,is_obsolete,
                            replaced_by,consider,alt_id,synonym,created_by, 
                            creation_date,comment,subset,property_value)
        elif(line.startswith("id: ")):
            HPid = line.rstrip("\n").split(": ")[1]
        elif(line.startswith("name: ")):
            name = line.rstrip("\n").split(": ")[1]
        elif(line.startswith("def: ")):
            definition = line.rstrip("\n").split("\"")[1]
        elif(line.startswith("synonym: ")):
            synonym.append( line.rstrip("\n").split("\"")[1])
        elif(line.startswith("is_a: ")):
            is_a.append( line.rstrip("\n").split(" ")[1])
        elif(line.startswith("alt_id: ")):
            alt_id.append( line.rstrip("\n").split(" ")[1])        
        elif(line.startswith("xref: ")):
            xref.append(line.rstrip("\n").split(" ")[1])
        elif(line.startswith("is_obsolete: ")):
            is_obsolete = True
        elif(line.startswith("consider: ")):
            consider.append(line.rstrip("\n").split(" ")[1])    
        elif(line.startswith("replaced_by: ")):
            replaced_by.append(line.rstrip("\n").split(" ")[1])
        elif(line.startswith("created_by: ")):
            created_by = line.rstrip("\n").split(" ")[1]
        elif(line.startswith("creation_date: ")):
            creation_date=line.rstrip("\n").split(" ")[1]
        elif(line.startswith("comment: ")):
            comment=line.rstrip("\n").split(": ")[1]
        elif(line.startswith("subset: ")):
            subset=line.rstrip("\n").split(" ")[1]
        elif(line.startswith("property_value: ")):
            property_value=line.rstrip("\n").split(": ")[1]
        print()

hpo_nodes = list(hpo_dg.nodes(data=True))
cnt_valid_term = 0
cnt_valid1 = 0
hpo_pred_hp0000001 = {}


for i in list(hpo_dg.predecessors('HP:0000001')):
    # print(str(i) + "  " + hpo_dg.nodes[i]['name'])
    hpo_pred_hp0000001[i] = 0

# print(str(hpo_pred_hp0000001))

with open('hpo_xref_data', 'w+') as fw:
    fw.write('HPO-ID'+'\t'+'EXTERNAL-NAME'+'\t'+'EXTERNAL-ID'+'\t'+'DATABASE-NAME'+'\n')
    for node in hpo_nodes:
        # ref_lst = []
        if(hpo_dg.nodes[node[0]]['is_obsolete'] == False):
            cnt_valid_term += 1
        if(len(hpo_dg.nodes[node[0]]['replaced_by']) <= 0 and len(hpo_dg.nodes[node[0]]['consider']) <= 0):
            cnt_valid1 += 1
        for subs in hpo_pred_hp0000001.keys():
            if(nx.algorithms.shortest_paths.generic.has_path(hpo_dg, node[0], subs)):
                hpo_pred_hp0000001[subs] += 1
        # print(node[1]['xref'])
        for i in range(len(node[1]['xref'])):
            term = node[1]['xref'][i].split(':')
            hpo_id = node[0]
            exter_name, exter_id = term[0].strip(), term[1].strip()

            fw.write(hpo_id+'\t'+exter_name+'\t'+exter_id+'\t'+'None')
            fw.write("\n")
        #
        # print(type(node[1]['xref']))
        # print(node[1]['xref'])
        # fw.write(str(node))
        # fw.write("\n")

# print("Total [Term]: " + str(cnt_term))
# print("valid [Term](is_obsolete = False): " + str(cnt_valid_term))
#
# print(str(hpo_pred_hp0000001))
# total = 0
# for i in hpo_pred_hp0000001.keys():
#     total += hpo_pred_hp0000001[i]
#
# print(str(total))
#
# print("valid [Term](len(replaced_by) = 0 and len(consider) = 0): " + str(cnt_valid1))
# print("hpo_dg lenth: " + str(nx.classes.function.number_of_nodes(hpo_dg)))
# print("hpo_dg directed or not: " + str(nx.classes.function.is_directed(hpo_dg)))
#
#
#
# hpo_dg.nodes['HP:0001250']
