FROM postgres:15
ENV POSTGRES_DB=db
ENV POSTGRES_USER=user
ENV POSTGRES_PASSWORD=password
ENV REPLICA_MODE=true
COPY init_repl.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init_repl.sh
EXPOSE 5432
