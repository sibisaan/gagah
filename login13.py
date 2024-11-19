import hashlib
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackContext
from telegram.ext.filters import Text
from urllib.parse import urlencode

# Token Telegram Bot Anda
TELEGRAM_API_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL API Mobile Legends untuk login
LOGIN_URL = 'https://api.mobilelegends.com/r'

# Stages untuk ConversationHandler
ROLEID, ZONEID, ACCOUNT, PASSWORD = range(4)

# Fungsi untuk meng-hash password menggunakan MD5
def md5_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

# Fungsi untuk login ke Mobile Legends API
def login_to_mobile_legends(roleid, zoneid, account, password):
    """
    Fungsi untuk mengirimkan data login ke API Mobile Legends.
    """
    # Hash password menggunakan MD5
    md5pwd = md5_hash(password)

    # Data login yang akan dikirim
    payload = {
        "accouent": account,       # Email atau Username
        "roleid": roleid,          # ID Akun
        "zoneid": zoneid,          # ID Server
        "md5pwd": md5pwd          # Password yang sudah di-hash
    }

    # Ubah data menjadi format x-www-form-urlencoded
    encoded_payload = urlencode(payload)

    # Headers untuk permintaan POST
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded',  # Pastikan ini menggunakan x-www-form-urlencoded
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
        'Origin': 'https://mtacc.mobilelegends.com',
        'Referer': 'https://mtacc.mobilelegends.com/',
        'X-Requested-With': 'com.mobile.legends',
    }

    # Kirimkan request POST
    response = requests.post(LOGIN_URL, data=encoded_payload, headers=headers)

    # Proses response dari server
    if response.status_code == 200:
        return response.text
    else:
        return f"Login failed with status code {response.status_code}"

# Handler untuk perintah /start
async def start(update: Update, context: CallbackContext) -> int:
    """
    Handler untuk perintah /start
    """
    await update.message.reply_text(
        'Selamat datang! Saya akan membantu Anda untuk login.\n\n' +
        '1. Masukkan roleid (ID Akun):'
    )
    return ROLEID

# Menerima Role ID
async def receive_roleid(update: Update, context: CallbackContext) -> int:
    """
    Menerima Role ID dan melanjutkan ke input Zone ID
    """
    context.user_data['roleid'] = update.message.text
    await update.message.reply_text('Role ID diterima. Sekarang masukkan zoneid (ID Server):')
    return ZONEID

# Menerima Zone ID
async def receive_zoneid(update: Update, context: CallbackContext) -> int:
    """
    Menerima Zone ID dan melanjutkan ke input email (account)
    """
    context.user_data['zoneid'] = update.message.text
    await update.message.reply_text('Zone ID diterima. Sekarang masukkan email Anda (account):')
    return ACCOUNT

# Menerima Account (email atau username)
async def receive_account(update: Update, context: CallbackContext) -> int:
    """
    Menerima account dan melanjutkan ke input password
    """
    context.user_data['account'] = update.message.text
    await update.message.reply_text('Account diterima. Sekarang masukkan password Anda (plain text):')
    return PASSWORD

# Menerima Password dan melakukan login
async def receive_password(update: Update, context: CallbackContext) -> int:
    """
    Menerima password dan memulai proses login
    """
    context.user_data['password'] = update.message.text  # Assume the password is plain text

    # Ambil data yang diperlukan
    roleid = context.user_data['roleid']
    zoneid = context.user_data['zoneid']
    account = context.user_data['account']
    password = context.user_data['password']

    # Proses login
    result = login_to_mobile_legends(roleid, zoneid, account, password)
    
    if "Login failed" not in result:
        await update.message.reply_text(f"Login berhasil!\nHasil: {result}")
    else:
        await update.message.reply_text(f"Login gagal!\nError: {result}")
    
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
            ROLEID: [MessageHandler(Text(), receive_roleid)],  # Terima Role ID
            ZONEID: [MessageHandler(Text(), receive_zoneid)],  # Terima Zone ID
            ACCOUNT: [MessageHandler(Text(), receive_account)],  # Terima Account
            PASSWORD: [MessageHandler(Text(), receive_password)],  # Terima Password
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conversation_handler)

    # Mulai bot
    application.run_polling()

if __name__ == '__main__':
    main()
