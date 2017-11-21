FROM ubuntu:14.04

RUN apt-get update \
    && apt-get install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
    build-essential \
    ca-certificates \
    gcc \
    git \
    libpq-dev \
    make \
    mercurial \
    pkg-config \
    python3.4 \
    python3.4-dev \
    ssh \
    libxml2-dev \
    libxslt1-dev \
    ruby \
    && apt-get autoremove \
    && apt-get clean

ADD https://raw.githubusercontent.com/pypa/pip/5d927de5cdc7c05b1afbdd78ae0d1b127c04d9d0/contrib/get-pip.py /root/get-pip.py
RUN python3.4 /root/get-pip.py
RUN pip3.4 install -U "setuptools==18.4"
RUN pip3.4 install -U "pip==7.1.2"
RUN pip3.4 install -U "virtualenv==13.1.2"

COPY ./*requirements.txt /app/
RUN pip3.4 install -r /app/dev-requirements.txt

COPY . /app
WORKDIR /app
