# ============================================================
# MedFlow Referral Agent - Dockerfile
# Multi-stage build for production-grade container
# Stage 1 — Builder: installs dependencies
# Stage 2 — Runtime: runs the application
# Python 3.11 — stable production version
# Non-root user — security best practice
# ============================================================

# ── Stage 1 — Builder ───────────────────────────────────────
# Full Python environment for installing dependencies
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building packages
# gcc and g++ needed for some Python packages with C extensions
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker layer caching
# If requirements.txt does not change — this layer is cached
# Speeds up builds significantly
COPY requirements.txt .

# Install all Python dependencies
# --no-cache-dir — do not cache pip downloads
# --user — install to user directory for copying to runtime
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2 — Runtime ───────────────────────────────────────
# Minimal Python environment — only what is needed to run
FROM python:3.11-slim AS runtime

# Set working directory
WORKDIR /app

# Create non-root user for security
# Running as root inside container is a security risk
# Real companies always run as non-root
RUN groupadd --gid 1000 medflow && \
    useradd --uid 1000 --gid medflow --shell /bin/bash --create-home medflow

# Copy installed packages from builder stage
# Only the compiled packages — not build tools
COPY --from=builder /root/.local /home/medflow/.local

# Copy application code
COPY src/ ./src/

# Copy startup script
COPY startup.sh ./startup.sh

# Set ownership to non-root user and make startup script executable
RUN chown -R medflow:medflow /app && chmod +x /app/startup.sh

# Switch to non-root user
USER medflow

# Add local packages to PATH
ENV PATH=/home/medflow/.local/bin:$PATH

# Environment variables with safe defaults
# Real values come from GCP Secret Manager at runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Expose port Cloud Run expects
EXPOSE 8080

# Health check — Cloud Run uses this to verify container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Start the application
CMD ["/app/startup.sh"]