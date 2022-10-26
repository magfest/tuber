FROM python:alpine as build

WORKDIR /app

RUN apk update && \
    apk add --no-cache postgresql-dev gcc python3-dev musl-dev g++ && \
    pip3 install flask && \
    rm -rf /var/lib/apt/lists/*

COPY . .

RUN python setup.py install

RUN rm -rf /usr/local/lib/python3.10/site-packages/pip \
    rm -rf /usr/local/lib/python3.10/site-packages/setuptools

FROM python:alpine

ENV DATABASE_URL=sqlite:///database.db
ENV FLASK_ENV=production
ENV REDIS_URL=
ENV WORKERS=2
ENV CIRCUITBREAKER_THREADS=2
ENV CIRCUITBREAKER_TIMEOUT=5
ENV ENABLE_CIRCUITBREAKER=false

COPY --from=build /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=build /usr/local/bin/tuber /usr/local/bin/tuber
COPY --from=build /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY entrypoint.sh entrypoint.sh

EXPOSE 8080

CMD /bin/sh entrypoint.sh
