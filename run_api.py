#!/usr/bin/env python3
"""
Run the REST API from project root so .env is loaded.
Usage: python run_api.py  (from project root)
"""
import os
import sys
from pathlib import Path

# Load .env first, before any imports that use env vars
root = Path(__file__).resolve().parent
os.chdir(root)
from dotenv import load_dotenv
load_dotenv(root / ".env")

sys.path.insert(0, str(root / "src"))
os.chdir(root / "src")

from api import app

port = int(os.environ.get("API_PORT", 8001))
print(f"Team Brain API on http://0.0.0.0:{port} (Elasticsearch)")
app.run(host="0.0.0.0", port=port, debug=False)
