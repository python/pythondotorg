FROM python:3.9-bullseye
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
RUN mkdir /code
WORKDIR /code
COPY dev-requirements.txt /code/
COPY base-requirements.txt /code/
RUN pip install -r dev-requirements.txt
COPY . /code/
