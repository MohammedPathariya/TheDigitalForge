FROM python:3.11.12-slim-bookworm

COPY sandbox/requirements.txt /tmp/sandbox-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/sandbox-requirements.txt

USER 65534:65534
WORKDIR /workspace
