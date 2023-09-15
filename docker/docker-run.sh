#!/bin/sh
export PATH="/venv/bin:$PATH"
/venv/bin/gunicorn --bind 0.0.0.0:8612 --access-logfile=- pollinate.wsgi:application
