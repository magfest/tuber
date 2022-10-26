FROM python:alpine as build

WORKDIR /app

RUN apk update && \
    apk add --no-cache postgresql-dev gcc python3-dev musl-dev g++ && \
    pip3 install flask && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# Workaround for https://github.com/scoder/lupa/issues/222
RUN pip3 install Cython && \
    pip3 install lupa --global-option="--with-cython"

RUN python setup.py install

RUN rm -rf /usr/local/lib/python3.11/site-packages/pip \
    rm -rf /usr/local/lib/python3.11/site-packages/setuptools

ENV DATABASE_URL=sqlite:///database.db
ENV FLASK_ENV=production
ENV REDIS_URL=
ENV WORKERS=2
ENV CIRCUITBREAKER_THREADS=2
ENV CIRCUITBREAKER_TIMEOUT=5
ENV ENABLE_CIRCUITBREAKER=false

COPY entrypoint.sh entrypoint.sh

EXPOSE 8080

CMD /bin/sh entrypoint.sh
