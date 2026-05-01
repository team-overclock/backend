#!/usr/bin/with-contenv bash

exec s6-setuidgid abc python3 /app/scripts/drop_tables.py "$@"
