
FROM alpine

WORKDIR /app
COPY . .
RUN apk update && apk add --no-cache python3 build-base && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools wheel && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

RUN apk update && apk add postgresql-dev python3-dev musl-dev
RUN pip install .
RUN pip install gunicorn
EXPOSE 8080

ENV DATABASE_URL=sqlite:///database.db
ENV FLASK_ENV=production
ENV SESSION_STORAGE=redis://6379
ENV JOB_STORAGE=redis://6379
ENV WORKERS=8

CMD /bin/sh entrypoint.sh
