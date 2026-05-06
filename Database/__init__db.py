import sqlite3
import os

def init_database():
    # Get the directory of the current script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'doctors.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the doctors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        address TEXT,
        phone TEXT
    )
    ''')

    # Local sample data for your project area
    sample_doctors = [
        ('Dr. Suresh Rao', 'Pulmonologist', 12.8706, 74.8427, 'Hampankatta, Mangaluru', '0824-2441111'),
        ('Dr. Priya Pai', 'Orthopedic', 12.8941, 75.0278, 'B.C Road, Bantwal', '0825-2332222'),
        ('Dr. John Dsouza', 'General Physician', 12.8751, 74.8441, 'KMC Hospital, Mangaluru', '0824-2223333')
    ]

    cursor.executemany('INSERT INTO doctors (name, specialty, lat, lon, address, phone) VALUES (?,?,?,?,?,?)', sample_doctors)
    
    conn.commit()
    conn.close()
    print(f"Database created at: {db_path}")

if __name__ == "__main__":
    init_database()