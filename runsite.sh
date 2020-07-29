#loginctl enable-linger $USER
#systemctl --user start docker
# can be replaced by docker-compose
docker run -v /Users/cl3720/python-workspace/Project_PhenCards/database:/database -d -p 5000:5000 phencards:test
