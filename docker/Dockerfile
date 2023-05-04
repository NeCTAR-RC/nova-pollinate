FROM python:3.10-slim-bullseye as build

WORKDIR /app
COPY . /app
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc && \
    ls /app && \
    python -m pip install -c https://releases.openstack.org/constraints/upper/zed -r /app/requirements.txt && \
    python -m pip install -c https://releases.openstack.org/constraints/upper/zed . && \
    python -m pip install -c https://releases.openstack.org/constraints/upper/zed gunicorn

FROM python:3.10-slim-bullseye AS release
COPY --from=build /venv /venv
COPY --from=build /app/docker/docker-run.sh /
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"
EXPOSE 8612
USER nobody
CMD ["/docker-run.sh"]
