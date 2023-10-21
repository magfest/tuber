FROM python:alpine as build

WORKDIR /app

RUN apk update && \
    apk add --no-cache postgresql-dev gcc python3-dev musl-dev g++ make && \
    pip3 install flask && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml pyproject.toml

# Workaround for https://github.com/scoder/lupa/issues/222
RUN pip3 install Cython && \
    pip3 install lupa==1.14.1 --global-option="--with-cython"


COPY tuber tuber
RUN pip install .

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
RUN addgroup --gid 1000 tuber && \
    adduser -D tuber -u 1000 --ingroup tuber 

FROM build as test
RUN apk update && \
    apk add --no-cache linux-headers postgresql && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /tuber/cov && \
    chown -R tuber:tuber /tuber/cov
COPY pyproject.toml pyproject.toml
RUN pip install .[test]
COPY tests tests
USER tuber

FROM build as release
RUN rm -rf /usr/local/lib/python3.11/site-packages/pip \
    rm -rf /usr/local/lib/python3.11/site-packages/setuptools
USER tuber
