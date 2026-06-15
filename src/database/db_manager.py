import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/meal_prep.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_db_connection():
    """Returns a functional state connection to the local database file."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;") # Enforce data relational safety
    conn.row_factory = sqlite3.Row            # Returns dictionary-like rows
    return conn

def init_db():
    """Reads the local schema.sql file and builds out tables."""
    # Ensure the data storage directory exists safely
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with open(SCHEMA_PATH, 'r') as f:
        schema_script = f.read()
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript(schema_script)
    conn.commit()
    conn.close()
    print("Database engine tables successfully initialized.")