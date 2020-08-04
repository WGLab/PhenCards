#loginctl enable-linger $USER
#systemctl --user start docker
# can be replaced by docker-compose
docker run -v /media/database:/database -d -p 5000:5000 phencards:test
