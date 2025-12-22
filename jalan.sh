#!/bin/bash

# --- KONFIGURASI ---
PORT=5000
SCRIPT_PY="bot.py"

echo "------------------------------------------"
echo "🚀 Memulai Flask dan Ngrok..."
echo "------------------------------------------"

# 1. Jalankan Flask di background
# Menggunakan '&' agar skrip lanjut ke baris berikutnya
python $SCRIPT_PY & 
FLASK_PID=$!

echo "✅ Flask berjalan di PID: $FLASK_PID"
sleep 2 # Memberi waktu Flask untuk startup

# 2. Jalankan Ngrok
echo "🌐 Menghubungkan ke Ngrok..."
ngrok http $PORT

# 3. Jika Ngrok dihentikan (CTRL+C), matikan juga Flask
kill $FLASK_PID
echo "👋 Semua proses dihentikan."
