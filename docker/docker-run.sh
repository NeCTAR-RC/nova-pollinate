#!/bin/bash -x

if [ -f /vault/secrets/secret_envs ]; then
    echo "** Loading secrets from /vault/secrets/secret_envs **"
    . /vault/secrets/secret_envs
else
    echo "** Secrets not found! **"
fi

gunicorn --bind 0.0.0.0:8612 --access-logfile=- pollinate.wsgi:application
