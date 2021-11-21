FROM python:alpine

WORKDIR /app

RUN apk update && \
    apk add --no-cache postgresql-dev gcc python3-dev musl-dev g++ && \
    pip3 install flask && \
    rm -rf /var/lib/apt/lists/*

COPY . .

ENV DATABASE_URL=sqlite:///database.db
ENV FLASK_ENV=production
ENV REDIS_URL=
ENV WORKERS=2
ENV CIRCUITBREAKER_THREADS=2
ENV CIRCUITBREAKER_TIMEOUT=5
ENV ENABLE_CIRCUITBREAKER=true

RUN python setup.py install

EXPOSE 8080

CMD /bin/sh entrypoint.sh
