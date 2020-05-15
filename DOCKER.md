# Droplet setup for Kai and Jim only

The information below is for documentation purposes only. Users do not need to use it, since the server set up and docker set up are already done.

To create DigitalOcean Droplet: Create a droplet in NYC region 3, with 2G mem and 50G storage with CentOS 7.8, no other configuration, then install docker exactly as in https://docs.docker.com/engine/install/centos/. (For CentOS 8, the instruction does not work if using yum, and install from source file instead)

After installing, make sure to do this postinstall step to add the docker group and individual users to the group.  https://docs.docker.com/engine/install/linux-postinstall/ (e.g. `sudo usermod -aG docker dongx4`). This is to allow dongx4 to run docker.

A user can start the docker service and enable linger with:
```
loginctl enable-linger $USER
systemctl --user start docker
```
or admin can with
```
systemctl start docker
```

--------------------

# Build PhenCards or site of choice in docker

PLEASE READ HOW TO CLEAN UP YOUR DOCKER IMAGES AT THE BOTTOM OF THIS FILE AFTER DOING ALL OF THIS.

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
Make sure everything you need is in your current folder and subdirectories if keeping `COPY . .` and all pip requirements are in `requirements.txt`. Minimally, need flask and redis in `requirements.txt`, but for PhenCards we have added several other packages.

Next to create the image (replace `phencards` with your site's name):

```
docker build -t phencards --network=host .
```

If you want to build an image with a more specific tag use:
`docker build -t phencards:test --network=host .`

To save the image to a TAR file to transfer to the main server `142.93.205.155`:

```
docker save --output phencards.tar phencards
```

# Run PhenCards or your site in docker

Load your image if you moved it from another server with:

```
docker load --input phencards.tar
```

Finally, to run the site via docker:

```
docker run -d -p 5003:5000 phencards
```

It should be at:

`http://142.93.205.155:5003`

If you want to run an image with a specific tag use:
`docker run -d -p 5001:5000 phencards:test`.

If you want to start a server in port 5001, the command `docker run -d -p 5001:5000 phencards` should be used.  This is because the first port value is the actual server port, the second one is _inside_ the actual docker container and should _always be_ 5000 unless you know specifically what ports you want to open in the docker container which can get more complex and requires further work.

To stop a docker container, check the container ID (something like `8a2652352336` when you `docker ps`), then do `docker stop 8a2652352336`. You can also use the shorthand name docker provides like "happy_platypus" or whatever name it assigns to the container.  Like `docker kill happy_platypus`.

# CLEANING UP DOCKER CONTAINERS AND IMAGES

```
docker container prune
docker rmi -f `docker images | grep "<none>" | awk {'print $3'}`
```
