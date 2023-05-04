#!/bin/sh
[ -f /vault/secrets/secret_envs ] && . /vault/secrets/secret_envs
export PATH="/venv/bin:$PATH"
gunicorn --bind 0.0.0.0:8612 --access-logfile=- pollinate.wsgi:application
