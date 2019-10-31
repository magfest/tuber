# Build Vue 
FROM node:lts-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Nginx
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY ./contrib/nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

#Flask
FROM python:alpine
ENV FLASK_APP tuber
ENV FLASK_CONFIG production
RUN apk add postgresql-dev gcc python3-dev musl-dev && pip3 install psycopg2
WORKDIR /app
COPY setup.py setup.py
RUN python -m venv venv
COPY tuber tuber
RUN venv/bin/pip install .
COPY migrations migrations
COPY app-start.sh .
# run-time configuration
EXPOSE 8080
ENTRYPOINT ["./app-start.sh"]
