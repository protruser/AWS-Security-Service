# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/shop
COPY requirements.txt .
RUN --mount=type=secret,id=pip_ca_bundle \
    if [ -f /run/secrets/pip_ca_bundle ]; then export PIP_CERT=/run/secrets/pip_ca_bundle; fi; \
    pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 shop
COPY --chown=shop:shop app ./app
COPY --chown=shop:shop templates ./templates
COPY --chown=shop:shop static ./static
COPY --chown=shop:shop run.py .
USER shop
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "30", "--error-logfile", "-", "run:app"]
