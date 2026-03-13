# Multi-stage Dockerfile for s3check
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy only files needed for build
COPY pyproject.toml setup.py README.md LICENSE ./
COPY src/ ./src/

# Build the package
RUN python -m build

# Final stage
FROM python:3.11-slim

# Metadata
LABEL maintainer="Yannis Duvignau <yduvignau@snapp.fr>"
LABEL description="s3check - Object Storage Access Verifier"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Copy the built package from builder
COPY --from=builder /app/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Create non-root user
RUN useradd -m -u 1000 s3check && \
    chown -R s3check:s3check /app

# Switch to non-root user
USER s3check

# Set entrypoint
ENTRYPOINT ["s3check"]

# Default command (can be overridden)
CMD ["--help"]
