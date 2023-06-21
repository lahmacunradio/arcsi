FROM nginx:1.25.1

# SSL through letsencrypt
RUN apk add --no-cache certbot

# Replace default files with custom configs
RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/
RUN rm /etc/nginx/conf.d/default.conf
COPY arcsi.conf /etc/nginx/conf.d/

# create dir for certificate auto-renewal
RUN mkdir /var/lib/certbot

# copy entrypoint and renewal script for container

COPY ./renew /etc/periodic/weekly/renew
RUN chmod +x /etc/periodic/weekly/renew

# HTTP+S reverse proxy
EXPOSE 80 443

# ENTRYPOINT in Docker compose file
