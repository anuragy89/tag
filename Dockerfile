FROM python:3.12-slim

# Build deps for tgcrypto C extension
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash botuser

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY bot.py database.py member_fetcher.py ./

RUN chown -R botuser:botuser /app

USER botuser

CMD ["python", "-u", "bot.py"]
