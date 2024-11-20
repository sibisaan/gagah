import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import hashlib
import requests

# Token Bot Telegram Anda
TELEGRAM_BOT_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL untuk GET request pertama untuk mendapatkan data login
LOGIN_URL = "https://mtacc.mobilelegends.com/v2.1/inapp/login-new"

# URL untuk mengirim permintaan POST login ke API Mobile Legends
LOGIN_API_URL = "https://accountmtapi.mobilelegends.com/"

# Headers yang diperlukan untuk GET dan POST requests
HEADERS = {
    "Host": "mtacc.mobilelegends.com",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Origin": "https://mtacc.mobilelegends.com",
    "Referer": "https://mtacc.mobilelegends.com/v2.1/inapp/login-new",
}

# Setup logging untuk debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Fungsi untuk melakukan GET request pertama untuk mendapatkan game token dan data lainnya
def get_initial_data():
    try:
        response = requests.get(LOGIN_URL, headers=HEADERS)
        if response.status_code == 200:
            logger.info("GET request successful!")
            try:
                # Coba untuk parse JSON
                data = response.json()
                ntf = data[0]["data"]["ntf"]  # Ambil ntf untuk game_token
                user_token = ntf.split(',')[0]  # Ambil userToken dari ntf
                return user_token  # Kembalikan user token
            except ValueError:
                # Jika tidak bisa parse JSON, tampilkan isi respons mentah
                logger.error(f"Error parsing JSON from response: {response.text}")
                return None
        else:
            logger.error(f"GET request failed. Status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error during GET request: {e}")
        return None

# Fungsi untuk meng-hash password menggunakan MD5
def md5_hash(password):
    return hashlib.md5(password.encode()).hexdigest()

# Fungsi untuk menghasilkan tanda tangan (sign) dinamis
def generate_sign(op, account, md5pwd, game_token, lang):
    data_string = f"{op}{account}{md5pwd}{game_token}{lang}"
    sign = hashlib.md5(data_string.encode()).hexdigest()
    return sign

# Fungsi untuk mengirim POST request untuk login
def post_login_request(user_token, email, md5_password):
    sign = generate_sign("login", email, md5_password, user_token, "id")
    data_to_send = {
        "op": "login",
        "sign": sign,
        "params": {
            "account": email,
            "md5pwd": md5_password,
            "game_token": user_token,
            "recaptcha_token": "",
            "country": "",
        },
        "lang": "id"
    }
    try:
        response = requests.post(LOGIN_API_URL, headers=HEADERS, json=data_to_send)
        if response.status_code == 200:
            logger.info("Login successful!")
            return response.json()  # Mengembalikan response JSON jika login berhasil
        else:
            logger.error(f"Login failed. HTTP Status Code: {response.status_code}")
            return response.text
    except Exception as e:
        logger.error(f"Error during POST request: {e}")
        return None

# Command handler untuk memulai percakapan
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome! Please enter your email:")

# Fungsi untuk menangani email, menyimpannya, dan kemudian meminta password
async def handle_email(update: Update, context: CallbackContext):
    user_email = update.message.text  # Mendapatkan email dari pengguna
    context.user_data['email'] = user_email  # Menyimpan email dalam user_data
    context.user_data['state'] = 'password'  # Ubah state menjadi 'password'
    await update.message.reply_text("Please enter your password:")

# Fungsi untuk menangani password dan login
async def handle_password(update: Update, context: CallbackContext):
    # Pastikan hanya password yang ditangani setelah email
    if context.user_data.get('state') != 'password':
        return

    user_password = update.message.text  # Mendapatkan password dari pengguna
    user_email = context.user_data.get('email')  # Mendapatkan email yang sudah disimpan

    # Mengecek apakah email sudah dimasukkan
    if not user_email:
        await update.message.reply_text("Please enter your email first.")
        return

    # Mengambil user_token dari GET request
    user_token = get_initial_data()

    if user_token:
        # Hash password menjadi MD5
        md5_password = md5_hash(user_password)
        # Melakukan login dengan mengirim POST request
        login_response = post_login_request(user_token, user_email, md5_password)

        if login_response:
            await update.message.reply_text(f"Login successful! Response: {login_response}")
        else:
            await update.message.reply_text("Login failed.")
        
        # Setelah password dimasukkan dan proses login selesai, reset state agar tidak meminta password lagi
        context.user_data['state'] = 'done'
    else:
        await update.message.reply_text("Failed to retrieve user token. Try again later.")

# Main function untuk menjalankan bot
def main():
    # Membuat aplikasi Telegram dengan token bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handler untuk /start command
    application.add_handler(CommandHandler("start", start))

    # Handler untuk email dan password
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
