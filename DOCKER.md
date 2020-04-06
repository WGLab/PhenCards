To create DigitalOcean Droplet:
Create a droplet in NYC region 3, with 2G mem and 50G storage with CentOS 7.8, no other configuration, then install docker exactly as in https://docs.docker.com/install/linux/docker-ce/centos/.

Make `Dockerfile` with this in it:
```
FROM python:3.7-alpine
WORKDIR /code
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run"]
```
Minimally, need flask and redis in `requirements.txt`.

Then

`curl -fsSL https://get.docker.com/rootless | sh` ([link to tutorial for this])(https://docs.docker.com/engine/security/rootless/)

Next
`export XDG_RUNTIME_DIR=/run/user/`id -u``
`export DOCKER_HOST=unix:///run/user/1002/docker.sock`
`systemctl --user start docker`

`docker build -t phencards --network=host .`

`docker run -d -p 5000:5000 phencards`

It should be at:

`http://142.93.205.155:5000`

When you login, you'll need to run (to keep the server running in BG after logout):

```
export XDG_RUNTIME_DIR=/run/user/`id -u`
export DOCKER_HOST=unix:///run/user/1002/docker.sock
loginctl enable-linger $USER
systemctl --user start docker
nohup docker run -d -p 5000:5000 phencards &
```

This has been conveniently saved into a file: `bash runsite.sh`.
