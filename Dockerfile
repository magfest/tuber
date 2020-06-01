
FROM node:11.12.0-alpine
COPY frontend/package*.json frontend/
RUN cd frontend && npm install
COPY frontend frontend
RUN cd frontend && npm run build

COPY backend backend
RUN apk update && apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN cd backend && pip install .
RUN pip install gunicorn
EXPOSE 8080
ENV DATABASE_URL=sqlite:///database.db
ENV FLASK_ENV=production
ENV STATIC_PATH=../../frontend/dist/
WORKDIR /backend
CMD gunicorn -b 0.0.0.0:8080 tuber.wsgi:app
