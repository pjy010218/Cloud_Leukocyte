FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    neo4j \
    flask \
    numpy \
    kubernetes

# Copy Source Code
COPY controller/ /app/controller/
COPY hierarchical_control/ /app/hierarchical_control/
COPY proactive_remediation/ /app/proactive_remediation/
COPY adaptive_security/ /app/adaptive_security/
COPY data_plane/ /app/data_plane/

ENV PYTHONPATH=/app

CMD ["python", "-u", "controller/main.py"]
