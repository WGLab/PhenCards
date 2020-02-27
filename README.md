# Project_PhenCards
Development of phencards.org web server for one stop shop of phenotype information
To run the Flask app locally:

cd into the directory   
do `pip install -r requirements.txt`  
do `python app.py`  
Got to localhost:5000 in your browser  
  
If you would like to use debug mode when adjusting the features, run the following:
  
cd into the directory  
do `export FLASK_DEBUG=1` for Linux and Mac, or `set FLASK_DEBUG=1` for Windows users  
do `FLASK run`  
Got to localhost:5000 in your browser, now you can monitor the changes in browser when changing the flusk code.  
  
Additional note: use `pip3` rather than `pip` since most systems have `pip` as part of python 2. To keep the server persistant, use `nohup python3 app.py &` to spin up the server.   

## Sqlite Database in Python
If you would like to connect to the `XXX.db` files directly using Python, just refer to the following example that helps to access SQL file in Python:
```
import sqlite3  
conn = sqlite3.connect("phenotype.db")  
cursor = conn.cursor()   
print("Opened database successfully")  
c = conn.cursor()  
cursor = c.execute("SELECT DISTINCT DiseaseName FROM PHENBASE")
```
Otherwise, if you have SQL Server, like Oracle or MySQL, you can also use those for opening db files.


## Database Source Tutorial


## External Resources
ICD10Data: https://www.icd10data.com   
OMIM: https://www.ncbi.nlm.nih.gov/omim   
Gene Ontology: http://geneontology.org  
UniProt: https://www.uniprot.org   

