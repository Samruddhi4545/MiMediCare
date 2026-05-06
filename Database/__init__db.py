import sqlite3

def init_database():
    # This creates the database file in your Database folder
    conn = sqlite3.connect('doctors.db')
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

    # Sample Local Data (Bantwal/Mangaluru area)
    # You can add real local clinics here!
    sample_doctors = [
        ('Dr. Suresh Rao', 'Pulmonologist', 12.8706, 74.8427, 'Hampankatta, Mangaluru', '0824-244xxxx'),
        ('Dr. Priya Pai', 'Orthopedic', 12.8941, 75.0278, 'B.C Road, Bantwal', '0825-233xxxx'),
        ('Dr. John Dsouza', 'General Physician', 12.8751, 74.8441, 'KMC Hospital, Mangaluru', '0824-222xxxx')
    ]

    cursor.executemany('INSERT INTO doctors (name, specialty, lat, lon, address, phone) VALUES (?,?,?,?,?,?)', sample_doctors)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with local GPS coordinates!")

if __name__ == "__main__":
    init_database()