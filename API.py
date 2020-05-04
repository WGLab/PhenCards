# use kegg API to get data

import requests


# input is the phenotype name, output is list([reference])
def kegg_api_reference(name):
    link = "http://rest.kegg.jp/find/disease/" + name.replace(' ', '+')
    # get the ID
    kegg_id = requests.get(link, verify=False).text[:9]
    link = "http://rest.kegg.jp/get/" + kegg_id
    res = requests.get(link, verify=False).text.splitlines()
    reference = []
    for i in range(len(res)):
        item = res[i]
        if item.startswith('REFERENCE'):
            reference.append(res[i:i+5])
    res = ''
    for ref in reference:
        ref = '\n'.join(ref)
        res += ref + '\n\n'
    return res


print(kegg_api_reference('cleft palate'))
