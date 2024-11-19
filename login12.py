import hashlib
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackContext
from telegram.ext.filters import Text

# Token Telegram Bot Anda
TELEGRAM_API_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL untuk login ke Mobile Legends API
LOGIN_URL = 'https://api.mobilelegends.com/r'

# Stages untuk ConversationHandler
EMAIL, ROLEID, ZONEID, PASSWORD = range(4)

# Fungsi untuk meng-hash password menggunakan MD5
def md5_hash(password: str) -> str:
    """Meng-hash password dengan MD5"""
    return hashlib.md5(password.encode()).hexdigest()

# Fungsi untuk login ke Mobile Legends API
def login_to_mobile_legends(account, roleid, zoneid, md5pwd):
    """
    Fungsi untuk mengirimkan data login ke API Mobile Legends secara sinkron.
    """
    # Payload login
    payload = {
        "accouent": account,  # Email pengguna
        "roleid": roleid,      # ID akun dalam game
        "zoneid": zoneid,      # ID server/zona
        "md5pwd": md5pwd      # Password yang sudah di-hash MD5
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
        'Origin': 'https://mtacc.mobilelegends.com',
        'Referer': 'https://mtacc.mobilelegends.com/'
    }

    # Melakukan permintaan POST untuk login
    response = requests.post(LOGIN_URL, data=payload, headers=headers)

    # Mengecek respons
    if response.status_code == 200:
        return response.json()  # Mengembalikan hasil login
    else:
        return {"error": "Login failed, please check your credentials."}  # Jika gagal

# Handler untuk perintah /start
async def start(update: Update, context: CallbackContext) -> int:
    """
    Handler untuk perintah /start
    """
    await update.message.reply_text(
        'Selamat datang! Saya akan membantu Anda untuk login.\n\n' +
        '1. Masukkan Email Anda\n' +
        '2. Masukkan Role ID Anda\n' +
        '3. Masukkan Zone ID Anda\n' +
        '4. Masukkan Password Anda'
    )
    return EMAIL

# Menerima Email
async def receive_email(update: Update, context: CallbackContext) -> int:
    """
    Menerima email dan melanjutkan ke input roleid
    """
    context.user_data['account'] = update.message.text
    await update.message.reply_text('Email diterima. Sekarang masukkan Role ID Anda.')
    return ROLEID

# Menerima Role ID
async def receive_roleid(update: Update, context: CallbackContext) -> int:
    """
    Menerima Role ID dan melanjutkan ke input zoneid
    """
    context.user_data['roleid'] = update.message.text
    await update.message.reply_text('Role ID diterima. Sekarang masukkan Zone ID Anda.')
    return ZONEID

# Menerima Zone ID
async def receive_zoneid(update: Update, context: CallbackContext) -> int:
    """
    Menerima Zone ID dan melanjutkan ke input password
    """
    context.user_data['zoneid'] = update.message.text
    await update.message.reply_text('Zone ID diterima. Sekarang masukkan password Anda.')
    return PASSWORD

# Menerima Password dan melakukan login
async def receive_password(update: Update, context: CallbackContext) -> int:
    """
    Menerima password, melakukan hash MD5 dan memulai proses login
    """
    # Mengambil data yang sudah dikumpulkan
    context.user_data['password'] = update.message.text  # Menerima password dalam bentuk plain text
    
    # Meng-hash password jika perlu
    md5pwd = md5_hash(context.user_data['password'])

    # Proses login ke server Mobile Legends
    result = login_to_mobile_legends(
        context.user_data['account'],
        context.user_data['roleid'],
        context.user_data['zoneid'],
        md5pwd
    )
    
    # Menampilkan hasil login di chat bot
    if "error" in result:
        await update.message.reply_text(f"Login gagal!\n{result['error']}")
    else:
        await update.message.reply_text(f"Login berhasil!\nHasil: {result}")

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
            EMAIL: [MessageHandler(Text(), receive_email)],
            ROLEID: [MessageHandler(Text(), receive_roleid)],
            ZONEID: [MessageHandler(Text(), receive_zoneid)],
            PASSWORD: [MessageHandler(Text(), receive_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conversation_handler)

    # Mulai bot
    application.run_polling()

if __name__ == '__main__':
    main()
