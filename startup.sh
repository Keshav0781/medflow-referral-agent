#!/bin/bash
# ============================================================
# MedFlow Referral Agent - Startup Script
# Runs RAG ingestion before starting the FastAPI server
# Ensures ChromaDB is populated on every container start
# ============================================================

set -e

echo "Starting MedFlow Referral Agent..."
echo "Step 1 — Running RAG ingestion to populate ChromaDB..."

python -m src.rag.ingestion

if [ $? -eq 0 ]; then
    echo "RAG ingestion completed successfully"
else
    echo "WARNING: RAG ingestion failed — starting server anyway"
    echo "Routing and urgency nodes will use empty context"
fi

echo "Step 2 — Starting FastAPI server..."
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080
