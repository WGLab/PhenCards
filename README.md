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
| INDEX | EXTERNAL-DATABASE-NAME  | SOURCE-LINK  | INSTRUCTIONS  |  COMMENTS |
|---|---|---|---|---|
| 1 | ICD-10  | ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2020/icd10cm_order_2020.txt  |    No permission required| Use the link to download  |
| 2  |  ICD-9 |  ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD-9/ucod.txt |    No permission required| Use the link to download  |
| 3  | ICD-O  | https://github.com/philipsales/icdoncology-3/blob/master/icd-oncology.v3.json  |    No permission required| Use the link to download  |
| 4  |  SNOMEDCT_US |https://download.nlm.nih.gov/umls/kss/IHTSDO20200131/SnomedCT_InternationalRF2_PRODUCTION_20200131T120000Z.zip |  If `account`/`password` is needed, use the following: `zhouy6`/`Zyy.1234WGlab` |  Need account information for download permission, around 500M|
| 5  | UMLS  | https://download.nlm.nih.gov/umls/kss/2019AB/umls-2019AB-full.zip  |  If `account`/`password` is needed, use the following: `zhouy6`/`Zyy.1234WGlab` |  Need account information for download permission, around 4GB; here is a useful tool to download using cluster: https://askubuntu.com/questions/29079/how-do-i-provide-a-username-and-password-to-wget|
| 6  | MeSH  | ftp://nlmpubs.nlm.nih.gov/online/mesh/MESH_FILES/xmlmesh/desc2020.gz  |    No permission required| Use the link to download  |
|  7 | DOID  |  http://purl.obolibrary.org/obo/doid.owl | No permission required  |  This is an HTML format file, need attention for parsing |
  
## Development Logic
Front-end files include `templates/index.html`, which is used to transfer input parameters from user; `templates/results.html`, which is used to generate result page with external links to other result pages inside `templates` folder. Another important part is `templetes/templete.html`, which is used for generate the overall templete of the whole front-end, other htmls are inheritated from this one. 
  
Back-end files include `API.py`, which is used to connect with APIs and return certain formated data sttructures; `app.py` which is the high-level framework built based on Flask; `forms.py`, `lib/json.py`, and `lib/json_format.py` are used for generate certain format we need for the presentation to users. 

## External Resources
ICD10Data: https://www.icd10data.com   
OMIM: https://www.ncbi.nlm.nih.gov/omim   
Gene Ontology: http://geneontology.org  
UniProt: https://www.uniprot.org   
  
## How to deploy the Docker image on DigitalOcean
[Documentation is here](DOCKER.md)
