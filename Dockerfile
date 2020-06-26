FROM amsterdam/python:3.8-buster
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

RUN apt-get update \
	&& apt-get install -y \
		libxml2-dev \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt \
	&& pip install uwsgi

WORKDIR /app
COPY requirements.txt /app/
COPY uwsgi.ini /app/
COPY test.sh /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY .flake8 /app/

COPY tips /app/tips
USER datapunt
CMD uwsgi --ini /app/uwsgi.ini
