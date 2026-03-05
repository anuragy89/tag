# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

# Copy & install Python deps into a prefix folder (clean layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install/deps --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root
RUN useradd --create-home --shell /bin/bash botuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install/deps /usr/local

# Copy bot source
COPY bot.py database.py member_fetcher.py ./

# Fix ownership
RUN chown -R botuser:botuser /app

USER botuser

# Health-check: just verify Python can import the bot module
HEALTHCHECK --interval=60s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import bot" || exit 1

# Heroku sets $PORT but we don't need it (polling bot, not HTTP)
# Keep CMD simple — Heroku reads heroku.yml for the actual command
CMD ["python", "-u", "bot.py"]
