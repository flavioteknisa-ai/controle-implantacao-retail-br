# -*- coding: utf-8 -*-
"""
WSGI entry point for Vercel deployment
"""
import os
import sys

# Ensure environment variables are loaded
if not os.environ.get('DATABASE_URL'):
    print("WARNING: DATABASE_URL not set, using SQLite fallback", file=sys.stderr)

from app import app, db

# Initialize database tables on first run
try:
    with app.app_context():
        db.create_all()
        print("✅ Database tables initialized", file=sys.stderr)
except Exception as e:
    print(f"⚠️ Warning: Could not initialize database: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    app.run()
