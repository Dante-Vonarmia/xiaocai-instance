FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=10

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --timeout 600 --retries 10 . "httpx>=0.24"

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys, urllib.request; urllib.request.urlopen('http://localhost:8001/health', timeout=3); sys.exit(0)" || exit 1

CMD ["python", "-m", "xiaocai_instance_api.main"]
