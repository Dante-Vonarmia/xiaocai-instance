FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=10

ARG PIP_INDEX_URL=""
ARG PIP_EXTRA_INDEX_URL=""
ARG PIP_TRUSTED_HOST=""

RUN set -eux; \
    set -- pip install --no-cache-dir --timeout 600 --retries 10; \
    if [ -n "$PIP_INDEX_URL" ]; then \
        set -- "$@" --index-url "$PIP_INDEX_URL"; \
    fi; \
    if [ -n "$PIP_EXTRA_INDEX_URL" ]; then \
        set -- "$@" --extra-index-url "$PIP_EXTRA_INDEX_URL"; \
    fi; \
    if [ -n "$PIP_TRUSTED_HOST" ]; then \
        set -- "$@" --trusted-host "$PIP_TRUSTED_HOST"; \
    fi; \
    set -- "$@" "flare-kernel==0.2.13" "flare-storage-adapters==0.1.3" "uvicorn>=0.30,<1.0"; \
    "$@"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys, urllib.request; urllib.request.urlopen('http://localhost:8000/kernel/health', timeout=3); sys.exit(0)" || exit 1

CMD ["python", "-m", "uvicorn", "flare_kernel.main:app", "--host", "0.0.0.0", "--port", "8000"]
