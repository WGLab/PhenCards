# Project_PhenCards
Development of phencards.org web server for one stop shop of phenotype information
To run the Flask app locally:

cd into the directory   
do `pip install -r requirements.txt`  
do `python3 app.py`  
Got to localhost:5000 in your browser  

Additional note: use `pip3` rather than `pip` since most systems have `pip` as part of python 2. To keep the server persistant, use `nohup python3 app.py &` to spin up the server. 

# External Resources Used
ICD10Data: https://www.icd10data.com   
OMIM: https://www.ncbi.nlm.nih.gov/omim   
Gene Ontology: http://geneontology.org  
UniProt: https://www.uniprot.org   
