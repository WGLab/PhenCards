# PhenCards
This is the repository for the code used to make [PhenCards.org](https://phencards.org)

(C) Wang Lab 2020-2021

## Running the site

We have uploaded Docker images for [PhenCards](https://hub.docker.com/r/genomicslab/phencards/tags?page=1&ordering=last_updated) (don't forget to use 1.0.0 for paper version), [Doc2Hpo](https://hub.docker.com/r/genomicslab/doc2hpo), and [Phen2Gene](https://hub.docker.com/r/genomicslab/phen2gene) at: https://hub.docker.com/u/genomicslab. You can click the links to find them as well.  You will also need the Docker image for [Elasticsearch 7.8.1](https://www.docker.elastic.co/r/elasticsearch/elasticsearch:7.8.1) which was used to build the Lucene indices and make the autocompletion and the site fast.

You need to set up certbot to get certificates to establish HTTPS for Doc2Hpo and communication with Phen2Gene and UMLS. You will need to use nginx or, as we did, httpd (Apache) to run services to create the site.  Thanks to the `docker-compose.yml` file, running `docker-compose build prod` builds the production version of the site using the Dockerfile and the code there.  Since you already have the docker images you can just run `docker-compose up -d prod` and it will run the Elasticsearch service and the Phen2Gene service for production.  If you want to edit the code in dev mode and see how it affects the site, use `docker-compose up -d app`. And you can see it change in real time on the `5010` port.  Production comes out the `5005` port.  Elasticsearch runs on the `9300` and `9200` ports.  Phen2Gene is locally run on the `6000` port and Doc2Hpo is run on the `7000` port.  However, for your purposes, you can use https://phen2gene.wglab.org and https://doc2hpo.wglab.org for the services on the site.  No real need to set up local Phen2Gene or Doc2Hpo.  As stated below, you will need to run `index_db.py` initially on the data from Zenodo to create the Lucene index database once you have your Elasticsearch service running. Then you should not have to run it again.  There are custom HTML, CSS, and JS templates for style on the site and these can be modified to your liking.

## To run the Flask app locally:

Make sure Python 3 is installed.
`cd` into the directory
run `pip install -r requirements.txt`  
run `python app.py`  
Go to `localhost:5005` in your browser  
  
If you would like to use debug mode when adjusting the features, run the following:
  
cd into the directory  
do `export FLASK_DEBUG=1` for Linux and Mac, or `set FLASK_DEBUG=1` for Windows users  
do `FLASK run`  
Got to localhost:5000 in your browser, now you can monitor the changes in browser when changing the Flask code.  
  
Additional note: use `pip3` rather than `pip` since most systems have `pip` as part of python 2. To keep the server persistent, use `nohup python3 app.py &` to spin up the server.   

## Elastic-search for autocompletion
The autocompletion feature is achieved by using `elastic-search-7.8.1` on the backend and implemented using jquery-ui (`esQuery.js`) on the frondend.
Install and start elastic-search first: `path-to-elastic-search/bin/elasticsearch`, and then modified and executed `index_db.py` to index the database documents from https://zenodo.org/record/4755959.
To avoid any CORS header issues, adding the following two lines in `path-to-elastic-search/config/elasticsearch.yml`
```
http.cors.enabled : true
http.cors.allow-origin : "*"
```
More details can be found in https://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters.html

## Development Logic
Front-end files include `templates/index.html`, which is used to transfer input parameters from user; `templates/results.html`, which is used to generate result page with external links to other result pages inside `templates` folder. Another important part is `templetes/templete.html`, which is used for generate the overall templete of the whole front-end, other htmls are inheritated from this one. 
  
Back-end files include `API.py`, which is used to connect with APIs and return formatted data structures; `app.py` is the high-level framework built for the app based on Flask; `queries.py` is used to execute local queries.
  
### How to deploy the Docker image on DigitalOcean in a basic way

[Documentation is here](DOCKER.md)
