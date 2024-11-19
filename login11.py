import hashlib
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackContext
from telegram.ext.filters import Text

# Token Telegram Bot Anda
TELEGRAM_API_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL API Mobile Legends untuk login
LOGIN_URL = 'https://accountmtapi.mobilelegends.com/'

# Stages untuk ConversationHandler
EMAIL, PASSWORD = range(2)

# Fungsi untuk meng-hash password menggunakan MD5
def md5_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

# Fungsi untuk login ke Mobile Legends API
def login_to_mobile_legends(account, md5pwd):
    """
    Fungsi untuk mengirimkan data login ke API Mobile Legends menggunakan email dan password.
    Mengembalikan `sign` dan `game_token` jika berhasil login.
    """
    # Payload login
    data = {
        "op": "login",
        "sign": "example_sign",  # Tanda tangan (sign) harus valid sesuai aturan API
        "params": {
            "account": account,
            "md5pwd": md5pwd,
            "game_token": "example_game_token",  # Ini bisa berubah, pastikan game_token yang valid
            "recaptcha_token": "",
            "country": ""
        },
        "lang": "id",
    }

    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
        'X-Requested-With': 'com.mobile.legends',
    }

    # Mengirimkan POST request ke API dengan requests
    response = requests.post(LOGIN_URL, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:  # Cek jika API mengembalikan code 0 (berhasil)
            sign = result.get('sign')
            game_token = result.get('game_token')
            return {"sign": sign, "game_token": game_token}
        else:
            # API mengembalikan error meskipun status 200
            return {"error": result.get('msg', 'Unknown error')}
    else:
        # Tangani error HTTP selain 200
        return {"error": f"HTTP Error {response.status_code}"}

# Handler untuk perintah /start
async def start(update: Update, context: CallbackContext) -> int:
    """
    Handler untuk perintah /start
    """
    await update.message.reply_text(
        'Selamat datang! Saya akan membantu Anda untuk login.\n\n' +
        '1. Masukkan Email (account)\n' +
        '2. Masukkan Password (md5pwd)'
    )
    return EMAIL

# Menerima Email
async def receive_email(update: Update, context: CallbackContext) -> int:
    """
    Menerima email dan melanjutkan ke input password (md5pwd)
    """
    context.user_data['account'] = update.message.text
    await update.message.reply_text('Email diterima. Sekarang masukkan password Anda (md5pwd).')
    return PASSWORD

# Menerima Password dan melakukan login
async def receive_password(update: Update, context: CallbackContext) -> int:
    """
    Menerima password dan memulai proses login
    """
    context.user_data['md5pwd'] = update.message.text  # Assume the password is MD5 encoded directly

    # Mengambil data yang sudah dikumpulkan
    account = context.user_data['account']
    md5pwd = md5_hash(context.user_data['md5pwd'])  # Hash password jika perlu

    # Proses login
    result = login_to_mobile_legends(account, md5pwd)
    
    if result:
        if 'error' in result:
            await update.message.reply_text(f"Login gagal: {result['error']}")
        else:
            sign = result.get("sign")
            game_token = result.get("game_token")
            await update.message.reply_text(f"Login berhasil!\nSign: {sign}\nGame Token: {game_token}")
    else:
        await update.message.reply_text("Login gagal! Periksa kembali kredensial Anda.")
    
    return ConversationHandler.END

# Handler untuk membatalkan percakapan
async def cancel(update: Update, context: CallbackContext) -> int:
    """
    Handler untuk membatalkan percakapan
    """
    await update.message.reply_text('Proses login dibatalkan.')
    return ConversationHandler.END

# Fungsi utama untuk menjalankan bot
def main():
    # Set up Application untuk Telegram Bot (v20+)
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()

    # Setup ConversationHandler untuk percakapan yang memerlukan beberapa input
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(Text(), receive_email)],  # Hanya menunggu email
            PASSWORD: [MessageHandler(Text(), receive_password)],  # Hanya menunggu password
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conversation_handler)

    # Mulai bot
    application.run_polling()

if __name__ == '__main__':
    main()
