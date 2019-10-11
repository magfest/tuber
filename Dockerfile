#Builx Vue
FROM node:latest as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY ./ .
RUN npm run build

#Deploy nginx
FROM nginx as production-stage
RUN mkdir /app
COPY --from=build-stage /app/dist /app
COPY /contrib/nginx.conf /etc/nginx/nginx.conf



# #Build backend Flask app
# FROM python:alpine
# COPY ./tuber /app
# WORKDIR /app
# RUN pip install -r requirements.txt
# EXPOSE 5000
# CMD python ./wsgi.py