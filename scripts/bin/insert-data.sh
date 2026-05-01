#!/usr/bin/with-contenv bash

exec s6-setuidgid abc python3 /app/scripts/insert_data.py /app/data "$@"
