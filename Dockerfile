FROM python:3.7-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /web
COPY . /web

RUN apk update
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    python3-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    linux-headers \
    musl-dev \
    postgresql-dev \
    ruby \
    ruby-rdoc \
    zlib-dev
RUN apk add git jpeg-dev libpq

RUN gem install bundler \
    && bundle install

RUN pip install pip --upgrade \
    && pip install -r dev-requirements.txt

RUN apk del .build-deps

ENTRYPOINT ["/web/entrypoint.sh"]
