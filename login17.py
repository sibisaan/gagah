import logging
import aiohttp
import asyncio
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Konfigurasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Konstanta untuk Telegram Bot
TELEGRAM_BOT_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL untuk mendapatkan fp (fingerprint)
GET_FINGERPRINT_URL = "https://mtacc.mobilelegends.com/v2.1/inapp/login-new"

# Status percakapan untuk bot
ROLEID, ZONEID, ACCOUNT, PASSWORD = range(4)

# Variabel global untuk menyimpan data
user_data = {}

# Fungsi untuk mendapatkan fingerprint dari server Mobile Legends
async def get_fingerprint():
    async with aiohttp.ClientSession() as session:
        # Mengirimkan permintaan GET untuk mendapatkan fingerprint
        async with session.get(GET_FINGERPRINT_URL) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                # Pastikan response berbentuk application/x-www-form-urlencoded
                if 'application/x-www-form-urlencoded' in content_type:
                    # Ambil response sebagai teks
                    url_encoded_response = await response.text()
                    logger.info(f"URL-encoded response: {url_encoded_response}")
                    
                    # Parse URL-encoded menjadi dictionary
                    parsed_data = urllib.parse.parse_qs(url_encoded_response)
                    logger.info(f"Parsed Data: {parsed_data}")
                    
                    # Ambil fp dari parsed_data
                    fp = parsed_data.get('fp', [None])[0]
                    logger.info(f"Fingerprint (fp): {fp}")
                    return fp
                else:
                    logger.error(f"Unexpected content type: {content_type}")
                    return None
            else:
                logger.error(f"Failed to get fingerprint. Status code: {response.status}")
                return None

# Fungsi untuk memulai percakapan
async def start(update: Update, context: CallbackContext) -> int:
    user_data.clear()  # Clear previous data
    user_data['chat_id'] = update.message.chat_id  # Simpan chat_id
    fp = await get_fingerprint()
    
    if fp:
        user_data['fp'] = fp
        await update.message.reply_text('Selamat datang! Saya akan membantu Anda untuk login.\n\n' +
                                       '1. Masukkan Role ID Anda')
        return ROLEID
    else:
        await update.message.reply_text('Gagal mendapatkan fingerprint. Coba lagi nanti.')
        return ConversationHandler.END

# Fungsi untuk meminta Role ID
async def roleid(update: Update, context: CallbackContext) -> int:
    roleid = update.message.text
    user_data['roleid'] = roleid
    await update.message.reply_text('Masukkan Zone ID Anda')
    return ZONEID

# Fungsi untuk meminta Zone ID
async def zoneid(update: Update, context: CallbackContext) -> int:
    zoneid = update.message.text
    user_data['zoneid'] = zoneid
    await update.message.reply_text('Masukkan Email Anda')
    return ACCOUNT

# Fungsi untuk meminta Email
async def account(update: Update, context: CallbackContext) -> int:
    account = update.message.text
    user_data['account'] = account
    await update.message.reply_text('Masukkan Password Anda (format MD5 otomatis akan diterapkan)')
    return PASSWORD

# Fungsi untuk menerima Password
async def password(update: Update, context: CallbackContext) -> int:
    password = update.message.text
    user_data['password'] = password  # Kita akan mengubah ini menjadi MD5 sebelum mengirim ke server
    
    # Ubah password menjadi MD5
    import hashlib
    md5_password = hashlib.md5(password.encode()).hexdigest()
    user_data['md5password'] = md5_password
    
    # Kirim data ke server Mobile Legends
    await send_to_server(update)
    return ConversationHandler.END

# Fungsi untuk mengirim data ke server Mobile Legends
async def send_to_server(update: Update) -> None:
    # Ambil data yang sudah dikumpulkan
    roleid = user_data['roleid']
    zoneid = user_data['zoneid']
    account = user_data['account']
    md5password = user_data['md5password']
    fp = user_data['fp']
    
    # Membuat payload untuk dikirim ke server Mobile Legends
    payload = {
        'roleid': roleid,
        'zoneid': zoneid,
        'account': account,
        'md5pwd': md5password,
        'sign': '',  # Anda perlu mengisi tanda tangan yang valid jika diperlukan
        'game_token': '',  # Token permainan
        'recaptcha_token': '',  # Jika ada verifikasi captcha
        'country': 'ID',  # Kode negara
        'lang': 'id',  # Bahasa Indonesia
        'fp': fp
    }

    # Kirim data ke server
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.mobilelegends.com/r", data=payload) as response:
            if response.status == 200:
                data = await response.text()
                await update.message.reply_text(f"Respons dari server:\n{data}")
            else:
                await update.message.reply_text(f"Gagal login. Status code: {response.status}")

# Fungsi utama untuk menjalankan bot
def main():
    # Setup Telegram bot dengan aplikasi
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Setup ConversationHandler untuk mengelola percakapan
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ROLEID: [MessageHandler(filters.TEXT & ~filters.COMMAND, roleid)],
            ZONEID: [MessageHandler(filters.TEXT & ~filters.COMMAND, zoneid)],
            ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, account)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
        },
        fallbacks=[],
    )

    # Menambahkan ConversationHandler ke dalam aplikasi
    application.add_handler(conv_handler)

    # Menjalankan bot
    application.run_polling()

# Menjalankan fungsi utama
if __name__ == '__main__':
    main()
