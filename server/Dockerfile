FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install minimal build deps for optional packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt \
    && pip install "psycopg2-binary>=2.9"

# Copy app sources
COPY . /app/server

EXPOSE 8001

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
