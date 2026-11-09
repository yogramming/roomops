# --------------------------------------------------
# Stage 1: Builder
# --------------------------------------------------
FROM python:3.14-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install runtime dependencies into an isolated directory.
COPY requirements.txt .

RUN python -m pip install \
    --prefix=/install \
    --no-cache-dir \
    -r requirements.txt


# --------------------------------------------------
# Stage 2: Runtime
# --------------------------------------------------
FROM python:3.14-slim-bookworm AS runtime
RUN python -m pip install --no-cache-dir --upgrade \
      pip \
      setuptools

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH"

WORKDIR /app

# Create an unprivileged application user.
RUN groupadd --system --gid 10001 roomops \
    && useradd --system --uid 10001 \
       --gid roomops \
       --home-dir /app \
       --no-create-home roomops

# Copy only installed runtime dependencies.
COPY --from=builder /install /usr/local

# Copy application code and migration configuration.
COPY --chown=roomops:roomops app/ ./app/
COPY --chown=roomops:roomops migrations/ ./migrations/
COPY --chown=roomops:roomops run.py .
COPY --chown=roomops:roomops pyproject.toml .
COPY --chown=roomops:roomops gunicorn.conf.py .

# Run as an unprivileged user.
USER 10001:10001

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]

