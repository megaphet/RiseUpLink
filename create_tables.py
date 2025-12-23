#!/usr/bin/env python
"""
Quick script to create all database tables.
Use this if you haven't run Flask-Migrate yet.

Usage:
  python create_tables.py
"""

from app import app, db

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('✓ All database tables created successfully.')
        print('✓ Your app is now ready to run.')
