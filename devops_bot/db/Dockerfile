FROM postgres:15
ENV POSTGRES_DB=db
ENV POSTGRES_USER=user
ENV POSTGRES_PASSWORD=password
COPY init_master.sql /docker-entrypoint-initdb.d/01_init_master.sql
COPY init_repl.sql /docker-entrypoint-initdb.d/02_init_replication.sql
EXPOSE 5432
