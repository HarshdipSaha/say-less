FROM python:3.12-slim-bookworm

# Hugging Face Spaces runs containers as uid 1000; the app writes its binder
# cache under corpus/, so that user has to own the app directory.
RUN useradd -m -u 1000 user
WORKDIR /app
# Run from source: sayless resolves corpus/surnames.txt relative to the repo
# layout, which a site-packages install would break.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user src ./src
COPY --chown=user app ./app
COPY --chown=user corpus/surnames.txt ./corpus/surnames.txt
RUN chown user /app
USER user

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
