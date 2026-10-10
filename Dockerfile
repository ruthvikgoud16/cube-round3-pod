FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Do not set ORCH_MODE=inproc here. That mode replays the sample catalog.
# A new unit runs only after a request supplies route and returned.
ENV OUT_DIR=/tmp/pod4-out \
    PYTHONUNBUFFERED=1

EXPOSE 8100

CMD ["sh", "-c", "uvicorn orchestration.api:app --host 0.0.0.0 --port ${PORT:-8100}"]
