FROM mysql:5.7

WORKDIR /

ENV MYSQL_ROOT_PASSWORD password 
ENV MYSQL_DATABASE web_tracking

COPY ./sql-scripts/ /docker-entrypoint-initdb.d/
