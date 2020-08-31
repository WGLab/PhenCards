FROM python:3.8-alpine
RUN apk --no-cache add musl-dev linux-headers g++ elasticsearch
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
WORKDIR /code
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
COPY . /code
RUN mkdir /media/database
RUN apk add --update \
    curl \
    && rm -rf /var/cache/apk/*
RUN chmod 755 /code/app_init.sh
ENTRYPOINT sh /code/app_init.sh
