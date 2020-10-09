#loginctl enable-linger $USER
#systemctl --user start docker
# use docker-compose now, site is too complex for just docker.
docker-compose up -d # to run everything and check for new builds
# to just re-up production app (prod) or dev (app)
#docker-compose up -d prod
# to build just one of the images
#docker-compose build prod
