# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install into /app/wheels so we can copy the exact site-packages dir
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --target=/app/packages -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN useradd --create-home --shell /bin/bash botuser

WORKDIR /app

# Copy installed packages from builder into site-packages
COPY --from=builder /app/packages /usr/local/lib/python3.12/site-packages

# Copy all bot source files
COPY bot.py database.py member_fetcher.py ./

RUN chown -R botuser:botuser /app

USER botuser

HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import telegram; import pyrogram; import motor" || exit 1

CMD ["python", "-u", "bot.py"]

