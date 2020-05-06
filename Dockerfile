
FROM node:11.12.0-alpine
WORKDIR /frontend
COPY . .
RUN npm install
RUN npm run build

WORKDIR /backend
COPY . .
RUN apk update && apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install .
RUN pip install gunicorn
EXPOSE 8080
CMD gunicorn -b 0.0.0.0:8080 tuber.wsgi:app
