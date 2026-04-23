import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, 'dermai.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_path TEXT,
            prediction_result TEXT,
            confidence_score REAL,
            risk_level TEXT,
            recommendation TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            city TEXT,
            specialization TEXT,
            contact TEXT
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM hospitals')
    if cursor.fetchone()[0] == 0:
        excel_path = os.path.join(PROJECT_DIR, 'hospitals', 'india_oncology_master.xlsx')
        if os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path)
                hospitals_to_insert = []
                for index, row in df.iterrows():
                    name = str(row.get('Hospital Name', ''))
                    city = str(row.get('City', ''))
                    # Provide defaults for missing info
                    specialization = 'Oncology'
                    contact = '1800-123-4567' # mock contact
                    if name and city and str(name).lower() != 'nan':
                        hospitals_to_insert.append((name, city, specialization, contact))
                
                cursor.executemany('''
                    INSERT INTO hospitals (name, city, specialization, contact) 
                    VALUES (?, ?, ?, ?)
                ''', hospitals_to_insert)
                print(f"Inserted {len(hospitals_to_insert)} hospitals into database.")
            except Exception as e:
                print("Error reading excel:", e)
        else:
            print("Excel file not found at", excel_path)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
