FROM rockylinux:8

# Install Python 3.9 (available in Rocky Linux 8)
RUN yum install -y python39 python39-pip gcc gcc-c++ git curl

# Use python3.9 explicitly
COPY requirements.txt requirements.txt
RUN python3.9 -m pip install --upgrade pip
RUN python3.9 -m pip install -r requirements.txt

WORKDIR /code
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
COPY . /code

RUN chown -R 1002:1002 /code

RUN mkdir /media/database
RUN chmod 755 /code/app_init.sh
ENTRYPOINT sh /code/app_init.sh
