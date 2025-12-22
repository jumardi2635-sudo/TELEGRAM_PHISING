import sqlite3

conn = sqlite3.connect('database.db')
conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        saldo INTEGER DEFAULT 0,
        telegram_id INTEGER UNIQUE
    )
''')
conn.close()
print("Database siap!")
