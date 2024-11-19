import requests
import hashlib
import json
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackContext, Update

# Token Telegram Bot Anda
TELEGRAM_API_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL API Mobile Legends
LOGIN_URL = 'https://accountmtapi.mobilelegends.com/'

def send_message_to_telegram(chat_id, message: str):
    """
    Fungsi untuk mengirim pesan ke Telegram
    """
    bot = Bot(token=TELEGRAM_API_TOKEN)
    bot.send_message(chat_id=chat_id, text=message)

def login_to_mobile_legends(email: str, password: str, chat_id: str):
    """
    Fungsi untuk mengirimkan data login ke API Mobile Legends dan menangani respons
    """
    # Hash password dengan MD5
    md5_password = hashlib.md5(password.encode()).hexdigest()

    # Payload login
    data = {
        "op": "login",
        "sign": "1f99b377af081e1912d3d5a72a1c3f55",  # Tanda tangan (sign) yang bisa di-generate berdasarkan algoritma tertentu
        "params": {
            "account": email,
            "md5pwd": md5_password,
            "game_token": "AaQk9TNfFDLJc88Bm_qWzQ7Ob9odew5avFD2Be2fwhmEmtYar7rY5mJmIKNcY2q3s5V0ERUOpjU",  # Pastikan game_token valid
            "recaptcha_token": "",
            "country": ""
        },
        "lang": "id"
    }

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
        'X-Requested-With': 'com.mobile.legends',
    }

    # Mengirimkan POST request ke API
    response = requests.post(LOGIN_URL, json=data, headers=headers)

    if response.status_code == 200:
        # Jika berhasil, proses respons
        result = response.json()
        # Mengirim hasil login ke bot Telegram
        send_message_to_telegram(chat_id, f"Login Berhasil!\nHasil: {json.dumps(result, indent=2)}")
        return result
    else:
        # Jika login gagal
        send_message_to_telegram(chat_id, f"Login Gagal!\nStatus Code: {response.status_code}")
        return None

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Selamat datang! Kirimkan email dan password untuk login.')

def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    # Asumsi inputnya adalah email dan password dipisahkan dengan spasi
    if '@' in user_message and ' ' in user_message:
        email, password = user_message.split(' ', 1)
        result = login_to_mobile_legends(email, password, update.message.chat.id)
        if result:
            update.message.reply_text(f"Login berhasil! Token: {result.get('token', 'Tidak ada token ditemukan.')}")
        else:
            update.message.reply_text("Login gagal! Periksa kembali kredensial.")
    else:
        update.message.reply_text("Format salah! Harap kirimkan email dan password dipisahkan dengan spasi.")

def main():
    # Set up updater dan dispatcher untuk Telegram Bot
    updater = Updater(token=TELEGRAM_API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Handler untuk perintah /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Handler untuk pesan teks biasa
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Mulai bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
