FROM python:3.12-slim-bookworm

WORKDIR /app
# Run from source: sayless resolves corpus/surnames.txt relative to the repo
# layout, which a site-packages install would break.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY app ./app
COPY corpus/surnames.txt ./corpus/surnames.txt

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
