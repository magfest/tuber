
FROM node AS build

WORKDIR /app
COPY . .
RUN npm install
RUN npm run build

FROM nginx:stable

COPY --from=build /app/dist /var/www
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# This is a hack around the envsubst nginx config. Because we have `$uri` set
# up, it would replace this as well. Now we just reset it to its original value.
ENV uri \$uri

# Default configuration
ENV PORT 8000
ENV SERVER_NAME _

CMD ["sh", "-c", "envsubst < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
