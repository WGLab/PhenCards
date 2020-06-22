#loginctl enable-linger $USER
#systemctl --user start docker
docker run -v /media/database:/media/database -d -p 5000:5000 phencards:test
