# #Build Vue
# FROM node:latest as build-stage
# WORKDIR /app
# COPY package*.json ./
# RUN npm install
# COPY ./ .
# RUN npm run build

# #Build nginx
# FROM nginx as production-stage
# RUN mkdir /app
# COPY --from=build-stage /app/dist /app
# COPY /contrib/nginx.conf /etc/nginx/nginx.conf

# FROM ubuntu:rolling
# COPY . /tuber
# RUN apt-get update -y && \
#     apt-get install -y python3-pip python3 python3-venv libpq-dev
# WORKDIR /tuber

FROM ubuntu:19.04
RUN apt-get update \
  && apt-get install -y python3-pip python3-dev python3 libpq-dev
COPY . /tuber
WORKDIR /tuber
RUN pip3 install .
CMD ["wsgi", "main:app"]