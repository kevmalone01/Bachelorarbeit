#!/usr/bin/env python3
"""
Migration script to add birth_place and nationality columns to clients table.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.db import db
from sqlalchemy import text

def migrate():
    """Add birth_place and nationality columns to clients table if they don't exist."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns exist (SQLite specific)
            result = db.session.execute(text('PRAGMA table_info(clients)'))
            columns = [row[1] for row in result.fetchall()]
            print('Existing columns:', columns)
            
            if 'birth_place' not in columns:
                print('Adding birth_place column...')
                db.session.execute(text('ALTER TABLE clients ADD COLUMN birth_place VARCHAR(100)'))
                db.session.commit()
                print('✓ birth_place column added')
            else:
                print('✓ birth_place column already exists')
            
            if 'nationality' not in columns:
                print('Adding nationality column...')
                db.session.execute(text('ALTER TABLE clients ADD COLUMN nationality VARCHAR(100)'))
                db.session.commit()
                print('✓ nationality column added')
            else:
                print('✓ nationality column already exists')
                
            print('Migration completed successfully!')
        except Exception as e:
            print(f'Error during migration: {e}')
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()

