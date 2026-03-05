FROM python:3.12-slim

# Install build deps needed for tgcrypto (C extension)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --create-home --shell /bin/bash botuser

WORKDIR /app

# Install Python dependencies normally (no --prefix / --target tricks)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY bot.py database.py member_fetcher.py ./

RUN chown -R botuser:botuser /app

USER botuser

# Verify all imports work at build time — catches missing modules immediately
RUN python -c "import telegram; import pyrogram; import motor; import database; import member_fetcher; print('All imports OK')"

CMD ["python", "-u", "bot.py"]
