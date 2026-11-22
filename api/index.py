"""
Vercel Serverless Entrypoint for AgroGuard AI (FastAPI).
Routes incoming HTTP requests to the main FastAPI application.
"""

import os
import sys

# Ensure root directory is on Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import and expose FastAPI app
from backend.main import app
