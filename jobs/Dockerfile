# Build from the repository root:  docker build -f jobs/Dockerfile -t gridqueue .
#
# One image, two uses:
#   API (default CMD):          docker run -p 8000:8000 gridqueue
#   Sweep (Serverless Job):     docker run gridqueue python /app/jobs/sweep_50_postcodes.py --stdout
#     (for a Nebius Serverless Job, pass the same as --container-command/--args; runbook in
#      reports/C-T24-PACKAGE.TASK_REPORT.md). The sweep writes $RUNS_DIR/sweep_summary.json and, with --stdout,
#      prints the full JSON so it is recoverable from the job logs.
# NOT YET BUILT OR RUN: no Docker in the environment where this was written.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    RUNS_DIR=/data/runs

WORKDIR /app
COPY backend/ /app/backend/
COPY jobs/ /app/jobs/
COPY data/ /app/data/
RUN pip install --no-cache-dir ./backend \
    && useradd --create-home --uid 10001 gridqueue \
    && mkdir -p /data/runs \
    && chown -R gridqueue /data

USER gridqueue
EXPOSE 8000
CMD ["gridqueue-api"]
