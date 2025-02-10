# This Dockerfile uses Docker Multi-Stage Builds
# See https://docs.docker.com/engine/userguide/eng-image/multistage-build/
# Requires Docker v17.05
# Base image for build and runtime
FROM python:3.12-slim-bookworm AS build

ARG VERSION
ENV PBR_VERSION=$VERSION

WORKDIR /app
COPY . /app

RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends build-essential gcc && \
    python -m venv /venv && \
    /venv/bin/python -m pip install -c https://releases.openstack.org/constraints/upper/2024.1 -r /app/requirements.txt && \
    /venv/bin/python -m pip install -c https://releases.openstack.org/constraints/upper/2024.1 gunicorn && \
    /venv/bin/python -m pip install -c https://releases.openstack.org/constraints/upper/2024.1 .

# Release build
FROM python:3.12-slim-bookworm

COPY --from=build /venv /venv
COPY --from=build /app/docker/docker-run.sh /

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8612
USER nobody
CMD ["/docker-run.sh"]
