#!/bin/bash
echo "Wait for master to be ready"
until PGPASSWORD=replicator_password pg_isready -h db -U replicator -d db; do
    sleep 2
done
echo "Creating backup"
rm -rf /var/lib/postgresql/data/*
PGPASSWORD=replicator_password pg_basebackup -h db -U replicator -D /var/lib/postgresql/data -P -R --slot=replication_slot
echo "Done. Start replica"
chmod 0700 /var/lib/postgresql/data
exec postgres
