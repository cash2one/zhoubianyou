FROM python:2.7-slim

# install libs
COPY ./collector/requirements.txt /
ADD ./jessie-sources.list /etc/apt/sources.list
RUN apt-get update \
    && apt-get install -y build-essential \
                          gettext \
                          git \
                          libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml \
                          libssl-dev zlib1g-dev \
    && pip install -r /requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    && apt-get purge -y build-essential git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# setup env
ENV SERVICE_PORT 8000
EXPOSE $SERVICE_PORT

ADD ./collector /code
WORKDIR /code

VOLUME ["/code/data"]

CMD "./run.sh"
