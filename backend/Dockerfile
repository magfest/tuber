FROM python:alpine

WORKDIR /app

RUN apk update && \
    apk add --no-cache postgresql-dev gcc python3-dev musl-dev linux-headers postgresql g++ && \
    pip3 install flask && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
COPY setup.py setup.py

# Workaround for https://github.com/scoder/lupa/issues/222
RUN pip3 install Cython && \
    pip3 install lupa --global-option="--with-cython"

RUN pip3 install -r requirements.txt

COPY tuber tuber
RUN python setup.py install

COPY requirements-test.txt requirements-test.txt
RUN pip3 install -r requirements-test.txt
COPY tests tests

RUN rm -rf /usr/local/lib/python3.11/site-packages/pip \
    rm -rf /usr/local/lib/python3.11/site-packages/setuptools

ENV DATABASE_URL=sqlite:///database.db
ENV FLASK_DEBUG=false
ENV REDIS_URL=
ENV WORKERS=2
ENV CIRCUITBREAKER_THREADS=2
ENV CIRCUITBREAKER_TIMEOUT=5
ENV ENABLE_CIRCUITBREAKER=false

EXPOSE 8080

COPY entrypoint.sh entrypoint.sh
CMD /bin/sh entrypoint.sh

RUN adduser -D tuber
USER tuber
