from database.db_manager import init_db, get_db_connection

def verify_system_health():
    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("\n--- Current Active Project Tables ---")
    for table in tables:
        print(f"Table Detected: {table['name']}")
        
    conn.close()

if __name__ == "__main__":
    verify_system_health()



