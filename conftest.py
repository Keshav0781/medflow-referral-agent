# ============================================================
# conftest.py — pytest configuration
# Adds project root to Python path
# Allows tests to import from src/ folder
# Must be in project root directory
# ============================================================

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))