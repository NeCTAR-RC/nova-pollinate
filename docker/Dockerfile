# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

EXPOSE 8612

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .

RUN apt-get update && apt-get install -y gcc

RUN python -m pip install -r requirements.txt
RUN python -m pip install gunicorn

WORKDIR /app
COPY . /app
COPY docker/docker-*.sh /

RUN python -m pip install -e /app && \
    chmod u+x /docker-*.sh

RUN useradd -u 42420 appuser && chown -R appuser /app
USER appuser

EXPOSE 80
CMD ["/docker-run.sh"]
