# PhenCards

Please cite our paper:

Havrilla, J.M., Liu, C., Dong, X., Weng, C., Wang, K. PhenCards: a data resource linking human phenotype information to biomedical knowledge. Genome Med 13, 91 (2021). https://doi.org/10.1186/s13073-021-00909-8

Zenodo for Code: [![DOI](https://zenodo.org/badge/238013852.svg)](https://zenodo.org/badge/latestdoi/238013852)

Zenodo for Data: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4755959.svg)](https://doi.org/10.5281/zenodo.4755959)

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

## Docker Deployment Troubleshooting

The following section addresses common deployment issues that may occur when setting up PhenCards with Docker, particularly for academic researchers deploying on different server environments.

### 1. Database Permissions Error

**Error:** `sqlite3.OperationalError: unable to open database file` or `PendingRollbackError`

**Cause:** Docker container user mismatch with host filesystem permissions for the SQLite database.

**Solution:**

1. **Check your user ID:**
```bash
id -u    # Note this number (e.g., 1000, 1002, etc.)
```

2. **Add user to docker-compose.yml for both app and prod services:**
```yaml
services:
  app:
    user: "YOUR_USER_ID:YOUR_USER_ID"  # e.g., "1002:1002"
    # ... rest of config
    
  prod:
    user: "YOUR_USER_ID:YOUR_USER_ID"  # e.g., "1002:1002" 
    # ... rest of config
```

3. **Fix database directory permissions:**
```bash
sudo mkdir -p /media/database
sudo chown -R $(id -u):$(id -g) /media/database/
sudo chmod 755 /media/database/
```

### 2. Elasticsearch Version Compatibility

**Error:** `TypeError: __init__() got an unexpected keyword argument 'timeout'` or `np.float_` AttributeError

**Cause:** Version mismatch between Elasticsearch server (7.8.1) and Python client library.

**Solution:** Ensure your `requirements.txt` includes:
```txt
elasticsearch==7.8.1
numpy<2.0.0
```

### 3. Elasticsearch URL Scheme Error

**Error:** `ValueError: URL must include a 'scheme', 'host', and 'port' component`

**Solution:** Update `config.py`:
```python
elasticsearch_url = "http://elasticsearch:9200"
```

### 4. Container Build Issues

**CentOS 7 Repository Errors:** If encountering repository errors during Docker build, consider updating the Dockerfile to use Rocky Linux 8:

```dockerfile
FROM rockylinux:8
RUN yum install -y python39 python39-pip gcc gcc-c++ git curl
# ... rest of Dockerfile
```

**File Permissions in Container:** If files exist but cannot be accessed in the production container, add to Dockerfile after `COPY . /code`:
```dockerfile
RUN chown -R 1002:1002 /code  # Use your actual user ID
```

### Quick Setup Script

For automated deployment setup:

```bash
#!/bin/bash
# setup.sh - Automated PhenCards deployment setup

echo "🔧 Setting up PhenCards with proper permissions..."

# Get current user info
USER_ID=$(id -u)
GROUP_ID=$(id -g)
echo "📋 Detected user ID: $USER_ID, group ID: $GROUP_ID"

# Create database directory with proper permissions
echo "📁 Setting up database directory..."
sudo mkdir -p /media/database
sudo chown -R $USER_ID:$GROUP_ID /media/database/
sudo chmod 755 /media/database/

# Update docker-compose.yml with current user (requires sed)
if command -v sed > /dev/null; then
    echo "⚙️ Updating docker-compose.yml with user permissions..."
    sed -i "s/user: \".*\"/user: \"$USER_ID:$GROUP_ID\"/" docker-compose.yml
    echo "✅ Updated docker-compose.yml"
else
    echo "⚠️ Please manually add 'user: \"$USER_ID:$GROUP_ID\"' to both app and prod services in docker-compose.yml"
fi

echo "✅ Setup complete! Run: docker-compose up -d"
```

Make it executable: `chmod +x setup.sh` and run: `./setup.sh`

### Notes for Academic Deployment

- **Production vs Development:** The `app` service includes live code mounting for development, while `prod` uses code built into the Docker image
- **Port Configuration:** Development runs on port 5005, production on port 5010 
- **Database Persistence:** The SQLite database at `/media/database/querycount.db` persists query logs across container restarts
- **Version Compatibility:** Always match Elasticsearch client library version (elasticsearch==7.8.1) with the server version for reliable operation
