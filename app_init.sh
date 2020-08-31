# while [[ "$(curl -s -o /dev/null -w '%{http_code}' elasticsearch:9200)" != "200" ]]; do sleep 1; done \
# && python index_db.py \
# && python app.py

# # skip db indexing.
while [[ "$(curl -s -o /dev/null -w '%{http_code}' elasticsearch:9200)" != "200" ]]; do sleep 1; done \
&& python app.py
