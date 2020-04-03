# code for running docker image site on DigitalOcean, you can logout after this.
export XDG_RUNTIME_DIR=/run/user/`id -u`
export DOCKER_HOST=unix:///run/user/1002/docker.sock
loginctl enable-linger $USER
systemctl --user start docker
nohup docker run -d -p 5000:5000 phencards &
