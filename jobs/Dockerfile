# Build from the repository root:  docker build -f jobs/Dockerfile -t gridqueue .
#
# PLACEHOLDER: the batch sweep (jobs/sweep.py, SPEC ticket C-T24) does not exist yet, so this image currently
# serves the API. Swap the CMD for `python -m jobs.sweep` once it lands.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    RUNS_DIR=/data/runs

WORKDIR /app
COPY backend/ /app/backend/
RUN pip install --no-cache-dir ./backend \
    && useradd --create-home --uid 10001 gridqueue \
    && mkdir -p /data/runs \
    && chown -R gridqueue /data

USER gridqueue
EXPOSE 8000
CMD ["gridqueue-api"]
