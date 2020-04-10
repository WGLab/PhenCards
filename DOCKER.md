# droplet setup

The information below is for documentation purposes only. Users do not need to use it, since the server set up and docker set up are already done.

To create DigitalOcean Droplet: Create a droplet in NYC region 3, with 2G mem and 50G storage with CentOS 7.8, no other configuration, then install docker exactly as in https://docs.docker.com/engine/install/centos/. (For CentOS 8, the instruction does not work if using yum, and install from source file instead)

After installing, make sure to do this postinstall step to add the docker group and individual users to the group.  https://docs.docker.com/engine/install/linux-postinstall/ (e.g. `sudo usermod -aG docker dongx4`). This is to allow dongx4 to run docker.

# docker 

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
Minimally, need flask and redis in `requirements.txt`, but for PhenCards we have added several other packages.

```
export XDG_RUNTIME_DIR=/run/user/`id -u`
export DOCKER_HOST=unix:///run/user/1002/docker.sock
```

Was a previous requirement that may no longer be necessary.

Next to create the image and test it:

```
systemctl --user start docker

docker build -t phencards --network=host .

docker run -d -p 5000:5000 phencards
```

It should be at:

`http://157.245.2.226:5000`

When you login, you'll need to run (to keep the server running in BG after logout):

```
loginctl enable-linger $USER
systemctl --user start docker
nohup docker run -d -p 5000:5000 phencards &
```

This has been conveniently saved into a file: `bash runsite.sh`.

To stop a docker container, check the container ID (something like `c954b6c89a4b081996ef34de6727317a1f270c20c6d3701823b30a59c6569505` when you `docker run`), then do `docker stop c954b6c89a4b081996ef34de6727317a1f270c20c6d3701823b30a59c6569505`.
