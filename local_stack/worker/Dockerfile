FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

COPY . /app
RUN pip install --no-cache-dir -r /app/local_stack/requirements.txt
CMD ["python", "-m", "local_stack.worker"]
