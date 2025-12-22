import sqlite3

# Membuat koneksi ke file database (akan otomatis dibuat jika belum ada)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 1. Membuat Tabel User
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        saldo INTEGER DEFAULT 0
    )
''')

# 2. Menambahkan 1 User Admin (Contoh Awal)
try:
    cursor.execute('''
        INSERT INTO users (username, password, full_name, saldo)
        VALUES ('admin', 'admin123', 'Administrator', 999999)
    ''')
    print("User admin berhasil dibuat!")
except sqlite3.IntegrityError:
    print("User admin sudah ada.")

conn.commit()
conn.close()
