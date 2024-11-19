import hashlib
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Token Telegram Bot Anda
TELEGRAM_API_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL API Mobile Legends untuk login
LOGIN_URL = 'https://accountmtapi.mobilelegends.com/'

# Stages untuk ConversationHandler
ID, SERVER, EMAIL, PASSWORD = range(4)

def login_to_mobile_legends(froleid, fzoneid, account, md5pwd):
    """
    Fungsi untuk mengirimkan data login ke API Mobile Legends.
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
        "froleid": froleid,   # ID Akun (froleid)
        "fzoneid": fzoneid    # Server Akun (zoneid)
    }

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
        'X-Requested-With': 'com.mobile.legends',
    }

    # Mengirimkan POST request ke API
    response = requests.post(LOGIN_URL, json=data, headers=headers)

    if response.status_code == 200:
        # Jika berhasil, proses respons
        result = response.json()
        return result
    else:
        # Jika login gagal
        return None

def start(update: Update, context: CallbackContext) -> int:
    """
    Handler untuk perintah /start
    """
    update.message.reply_text('Selamat datang! Saya akan membantu Anda untuk login.\n\n' +
                              '1. Masukkan ID Akun Anda (froleid)\n2. Masukkan Server Akun Anda (fzoneid)\n3. Masukkan Email (account)\n4. Masukkan Password (md5pwd)')
    return ID

def receive_account_id(update: Update, context: CallbackContext) -> int:
    """
    Menerima ID Akun dan melanjutkan ke input server (fzoneid)
    """
    context.user_data['froleid'] = update.message.text
    update.message.reply_text('ID Akun diterima. Sekarang masukkan Server Akun (fzoneid) Anda.')
    return SERVER

def receive_server(update: Update, context: CallbackContext) -> int:
    """
    Menerima Server Akun (fzoneid) dan melanjutkan ke input email (account)
    """
    context.user_data['fzoneid'] = update.message.text
    update.message.reply_text('Server diterima. Sekarang masukkan email Anda (account).')
    return EMAIL

def receive_email(update: Update, context: CallbackContext) -> int:
    """
    Menerima email dan melanjutkan ke input password (md5pwd)
    """
    context.user_data['account'] = update.message.text
    update.message.reply_text('Email diterima. Sekarang masukkan password Anda (md5pwd).')
    return PASSWORD

def receive_password(update: Update, context: CallbackContext) -> int:
    """
    Menerima password dan memulai proses login
    """
    context.user_data['md5pwd'] = update.message.text  # Assume the password is MD5 encoded directly
    
    # Mengambil data yang sudah dikumpulkan
    froleid = context.user_data['froleid']
    fzoneid = context.user_data['fzoneid']
    account = context.user_data['account']
    md5pwd = context.user_data['md5pwd']

    # Proses login
    result = login_to_mobile_legends(froleid, fzoneid, account, md5pwd)
    
    if result:
        # Menampilkan hasil login di chat bot
        update.message.reply_text(f"Login berhasil!\nHasil: {result}")
    else:
        update.message.reply_text("Login gagal! Periksa kembali kredensial Anda.")
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """
    Handler untuk membatalkan percakapan
    """
    update.message.reply_text('Proses login dibatalkan.')
    return ConversationHandler.END

def main():
    # Set up updater dan dispatcher untuk Telegram Bot
    updater = Updater(token=TELEGRAM_API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Setup ConversationHandler untuk percakapan yang memerlukan beberapa input
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ID: [MessageHandler(Filters.text & ~Filters.command, receive_account_id)],
            SERVER: [MessageHandler(Filters.text & ~Filters.command, receive_server)],
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, receive_email)],
            PASSWORD: [MessageHandler(Filters.text & ~Filters.command, receive_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conversation_handler)

    # Mulai bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
