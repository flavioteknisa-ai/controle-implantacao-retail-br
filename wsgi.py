# -*- coding: utf-8 -*-
"""
WSGI entry point for Vercel deployment
"""
import os

# Ensure environment variables are loaded
if not os.environ.get('DATABASE_URL'):
    print("WARNING: DATABASE_URL not set, using SQLite fallback")

from app import app

if __name__ == "__main__":
    app.run()
