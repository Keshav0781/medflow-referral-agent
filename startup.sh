#!/bin/bash
# ============================================================
# MedFlow Referral Agent - Startup Script
# ChromaDB data is pre-baked into the Docker image
# Just starts the FastAPI server
# ============================================================

set -e

echo "Starting MedFlow Referral Agent..."
echo "ChromaDB data pre-baked into image — skipping ingestion"
echo "Starting FastAPI server..."

exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080
