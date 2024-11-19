import logging
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Menentukan log level
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define conversation states
ROLEID, ZONEID, EMAIL, PASSWORD = range(4)

# Global variable to store user input data
user_data = {}

# URL untuk GET request untuk mendapatkan fingerprint
GET_FINGERPRINT_URL = 'https://mtacc.mobilelegends.com/v2.1/inapp/login-new'

# URL untuk POST request untuk login
LOGIN_URL = 'https://api.mobilelegends.com/r'


async def get_fingerprint(session):
    """Mengirimkan GET request untuk mendapatkan fingerprint."""
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Cookie': 'userId=884785129; userGroup=12508',
        'Host': 'mtacc.mobilelegends.com',
        'Referer': 'https://mtacc.mobilelegends.com/v2.1/',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
        'X-Requested-With': 'com.mobile.legends'
    }

    async with session.get(GET_FINGERPRINT_URL, headers=headers) as response:
        if response.status == 200:
            # Dapatkan fingerprint dari respons, Anda bisa menyesuaikan sesuai respons yang diterima
            # Respons adalah URL encoded, jadi kita ambil teks respons terlebih dahulu
            text_response = await response.text()
            # Mengambil fp dari respons URL encoded
            fingerprint = text_response.split('fingerprint=')[1].split('&')[0]  # Sesuaikan sesuai dengan format respons
            return fingerprint
        else:
            logger.error(f'Failed to get fingerprint, status: {response.status}')
            return None


async def login_to_game(session, roleid, zoneid, email, password, fingerprint):
    """Mengirimkan POST request untuk login dengan data yang diperlukan."""
    payload = {
        'roleid': roleid,
        'zoneid': zoneid,
        'accouent': email,
        'md5pwd': password,  # Pastikan password sudah dalam format MD5
        'fp': fingerprint,    # Gunakan fingerprint yang didapat dari GET request
        'sign': 'sign_value_here',  # Sign yang perlu dihitung sebelumnya, bisa menggunakan metode tertentu
        'game_token': 'game_token_here',  # Token permainan, jika sudah tersedia
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
    }

    async with session.post(LOGIN_URL, data=payload, headers=headers) as response:
        if response.status == 200:
            response_text = await response.text()
            return response_text
        else:
            logger.error(f'Login failed, status: {response.status}')
            return None


async def start(update: Update, context: CallbackContext):
    """Handler untuk command /start"""
    user_data.clear()
    user_data['roleid'] = None
    await update.message.reply("Masukkan Role ID Anda:")

    return ROLEID


async def receive_roleid(update: Update, context: CallbackContext):
    """Handler untuk menerima roleid"""
    user_data['roleid'] = update.message.text
    await update.message.reply("Masukkan Zone ID Anda:")
    return ZONEID


async def receive_zoneid(update: Update, context: CallbackContext):
    """Handler untuk menerima zoneid"""
    user_data['zoneid'] = update.message.text
    await update.message.reply("Masukkan Email Anda:")
    return EMAIL


async def receive_email(update: Update, context: CallbackContext):
    """Handler untuk menerima email"""
    user_data['email'] = update.message.text
    await update.message.reply("Masukkan Password Anda:")
    return PASSWORD


async def receive_password(update: Update, context: CallbackContext):
    """Handler untuk menerima password dan melanjutkan ke proses login"""
    user_data['password'] = update.message.text
    # Melakukan GET untuk mendapatkan fingerprint
    async with aiohttp.ClientSession() as session:
        fingerprint = await get_fingerprint(session)
        if fingerprint:
            # Jika fingerprint berhasil didapat, lakukan login
            login_response = await login_to_game(session, user_data['roleid'], user_data['zoneid'],
                                                  user_data['email'], user_data['password'], fingerprint)
            if login_response:
                await update.message.reply(f"Login berhasil!\n{login_response}")
            else:
                await update.message.reply("Login gagal. Silakan coba lagi.")
        else:
            await update.message.reply("Gagal mendapatkan fingerprint, login tidak dapat dilakukan.")

    return ConversationHandler.END


def main():
    """Set up the Telegram bot and handlers"""
    application = Application.builder().token("7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw").build()

    # Define conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ROLEID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_roleid)],
            ZONEID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_zoneid)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
        },
        fallbacks=[],
    )

    # Add conversation handler to application
    application.add_handler(conversation_handler)

    # Run the bot
    application.run_polling()


if __name__ == '__main__':
    main()
