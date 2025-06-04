#!/bin/sh
export PATH="/venv/bin:$PATH"
gunicorn --bind :8080 --access-logfile=- --worker-tmp-dir /dev/shm --forwarded-allow-ips '*' --access-logformat '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' --workers 3 pollinate.wsgi:application
