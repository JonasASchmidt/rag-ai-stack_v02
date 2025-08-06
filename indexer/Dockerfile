FROM python:3.12-slim

WORKDIR /app

# Install only the dependencies required for ingestion
COPY indexer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the indexer package and the core library
COPY core /app/core
COPY indexer /app/indexer

CMD ["python", "-m", "indexer.watcher"]
