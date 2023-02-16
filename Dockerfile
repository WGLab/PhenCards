FROM centos/python-38-centos7
USER root
RUN yum install musl-dev linux-headers g++ gcc elasticsearch git curl
RUN yum clean all
# Install miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
     /bin/bash ~/miniconda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
RUN conda install sqlite
WORKDIR /code
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
COPY . /code
RUN mkdir /media/database
RUN chmod 755 /code/app_init.sh
ENTRYPOINT sh /code/app_init.sh
