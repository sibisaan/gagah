import hashlib
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ConversationHandler
from telegram.ext.filters import Text
import json

# Token Telegram Bot Anda
TELEGRAM_API_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL API Mobile Legends
GET_FINGERPRINT_URL = 'https://mtacc.mobilelegends.com/v2.1/inapp/login-new'
LOGIN_URL = 'https://api.mobilelegends.com/r'

# Stages untuk ConversationHandler
ROLEID, ZONEID, ACCOUNT, PASSWORD = range(4)

# Fungsi untuk mendapatkan fingerprint
async def get_fingerprint():
    async with aiohttp.ClientSession() as session:
        async with session.get(GET_FINGERPRINT_URL) as response:
            if response.status == 200:
                # Ambil fp dari respons JSON
                json_response = await response.json()
                fp = json_response.get('fp', '')
                return fp
            return None

# Fungsi untuk meng-hash password menggunakan MD5
def md5_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

# Fungsi untuk login ke Mobile Legends API
async def login_to_mobile_legends(roleid, zoneid, account, md5pwd, fp):
    data = {
        "fp": fp,
        "type": "event",
        "data": {
            "act_type": "mtacc",
            "proj": "mlbb",
            "behavior": "click_login",
            "account": account,
            "os_platform": "Android",
            "os_version": "11",
            "phone_brand": "other",
            "browser_brand": "chrome",
            "browser_version": "130.0.6723.107",
            "browser_engine": "webkit",
            "ga": ""
        },
        "zoneid": zoneid,
        "roleid": roleid
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(LOGIN_URL, json=data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result
            return None

# Handler untuk perintah /start
async def start(update: Update, context: CallbackContext) -> int:
    fp = await get_fingerprint()
    if not fp:
        await update.message.reply_text("Gagal mendapatkan fingerprint. Coba lagi nanti.")
        return ConversationHandler.END
    
    context.user_data['fp'] = fp  # Menyimpan fp yang didapat

    await update.message.reply_text(
        'Selamat datang! Saya akan membantu Anda untuk login.\n\n' +
        '1. Masukkan Role ID Anda'
    )
    return ROLEID

# Menerima Role ID
async def receive_roleid(update: Update, context: CallbackContext) -> int:
    context.user_data['roleid'] = update.message.text
    await update.message.reply_text('Role ID diterima. Sekarang masukkan Zone ID Anda.')
    return ZONEID

# Menerima Zone ID
async def receive_zoneid(update: Update, context: CallbackContext) -> int:
    context.user_data['zoneid'] = update.message.text
    await update.message.reply_text('Zone ID diterima. Sekarang masukkan email Anda (account).')
    return ACCOUNT

# Menerima Email
async def receive_account(update: Update, context: CallbackContext) -> int:
    context.user_data['account'] = update.message.text
    await update.message.reply_text('Email diterima. Sekarang masukkan password Anda (dalam format biasa).')
    return PASSWORD

# Menerima Password dan melakukan login
async def receive_password(update: Update, context: CallbackContext) -> int:
    context.user_data['password'] = update.message.text  # Password dalam format biasa
    
    # Mengambil data yang sudah dikumpulkan
    roleid = context.user_data['roleid']
    zoneid = context.user_data['zoneid']
    account = context.user_data['account']
    md5pwd = md5_hash(context.user_data['password'])  # Hash password menjadi MD5
    fp = context.user_data['fp']  # Fingerprint yang didapat

    # Proses login
    result = await login_to_mobile_legends(roleid, zoneid, account, md5pwd, fp)
    
    if result:
        await update.message.reply_text(f"Login berhasil!\nHasil: {json.dumps(result, indent=4)}")
    else:
        await update.message.reply_text("Login gagal! Periksa kembali kredensial Anda.")
    
    return ConversationHandler.END

# Handler untuk membatalkan percakapan
async def cancel(update: Update, context: CallbackContext) -> int:
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
            ROLEID: [MessageHandler(Text(), receive_roleid)],
            ZONEID: [MessageHandler(Text(), receive_zoneid)],
            ACCOUNT: [MessageHandler(Text(), receive_account)],
            PASSWORD: [MessageHandler(Text(), receive_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conversation_handler)

    # Mulai bot
    application.run_polling()

if __name__ == '__main__':
    main()
