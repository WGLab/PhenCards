database = set()
res = []
for line in open("hpo.obo"):
    if line[:6] == 'xref: ':
        target = line[6:]
        idx = target.find(':')
        database.add(target[:idx])
for i in database:
    res.append(i)
res.sort()
for i in res:
    print(i)
