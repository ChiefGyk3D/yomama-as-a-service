# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0

# Multi-stage build for YoMama-as-a-Service
# The base image is pinned by digest so a rebuild is reproducible and a
# retagged upstream image cannot slip in; Dependabot moves the digest.
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2 AS builder

# Update OS packages and install build dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        gcc=4:14.2.0-1 \
        g++=4:14.2.0-1 \
        make=4.4.1-2 \
        libffi-dev=3.4.8-2 \
        libssl-dev=3.5.7-1~deb13u3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir --require-hashes -r requirements.txt

# Final stage
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2

# Update OS packages in final stage
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates=20250419 \
        curl=8.14.1-2+deb13u5 \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Dedicated non-root user. The compose deployment has no volumes, so UID/GID
# 1000 is just the conventional first unprivileged account.
RUN groupadd --gid 1000 yomama \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash yomama

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# The runtime image has no use for pip. pip 26.x vendors msgpack 1.1.2 and
# setuptools 70.3.0 (pkg_resources) and ships an SBOM naming them, which Trivy
# reports as GHSA-6v7p-g79w-8964, CVE-2025-47273 and CVE-2026-59890 even
# though neither package is installed. No pip release carries patched copies
# yet, so the final stage drops pip; the builder keeps it.
RUN python -m pip uninstall -y pip

# Copy application code
COPY --chown=yomama:yomama main.py .
COPY --chown=yomama:yomama demo.py .
COPY --chown=yomama:yomama yo_mama/ ./yo_mama/

# Switch to non-root user
USER 1000:1000

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import sys; sys.exit(0)"]

# Default command (can be overridden)
CMD ["python", "main.py"]
