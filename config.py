import os

dirname = os.path.dirname(__file__)

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    path_to_phenotypedb = '/media/database/phenotype.db'
    doc2hpo_default = "Individual II-2 is a 9 years old girl. She does not have microcephaly. She was born at term, also with normal birth parameters. She began to stand at 11 months, walk with aid at 13 months, and speak at 17 months. At age 5, she was just like other children of similar age, with the ability to dress and sing, and count by herself. Starting at 6 years of age, she began to show regression of developmental patterns: she could not dress by herself anymore, and could not express even a single sentence or count numbers. Clinical examination revealed a coarse face with low anterior and posterior hairlines, prominent frontal bossing, thick eyebrows, synophrys (unibrow), hypertelorism, and thick lips. Growth parameters were normal. Her clinical course was also severe, with progressive neurodegeneration, behavioral problems (including hyperactivity, impulsivity, obstinacy, anxious behaviors and autistic-like behaviors), and hearing loss. The diagnosis of severe intellectual disability was made, based on Wechsler Intelligence Scale examination. Measuring activities of daily living showed extreme disability. Brain MRI demonstrated cortical atrophy with enlargement of the subarachnoid spaces and ventricular dilatation (Figure 2). Brainstem evoked potentials showed moderate abnormalities. EEG recording showed abnormal sleep EEG, just like her brother’s manifestation."
    doc2hpo_url = "http://doc2hpo.wglab.org/parse/acdat" #"http://impact2.dbmi.columbia.edu/doc2hpo/parse/acdat" # can return to HTTPS when Columbia renews SSL cert and fixes site permanently
    elasticsearch_url = "elasticsearch:9200"
    path_to_headers = os.path.join(dirname, 'static/text/headers.txt')

