FROM nginx:1.18-alpine

RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/
RUN rm /etc/nginx/conf.d/default.conf
COPY arcsi.conf /etc/nginx/conf.d/
EXPOSE 80
