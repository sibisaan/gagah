import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
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
            print("GET request successful!")
            data = response.json()
            ntf = data[0]["data"]["ntf"]  # Ambil ntf untuk game_token
            user_token = ntf.split(',')[0]  # Ambil userToken dari ntf
            return user_token  # Kembalikan user token
        else:
            print(f"GET request failed. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error during GET request: {e}")
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
            print("Login successful!")
            return response.json()  # Mengembalikan response JSON jika login berhasil
        else:
            print(f"Login failed. HTTP Status Code: {response.status_code}")
            return response.text
    except Exception as e:
        print(f"Error during POST request: {e}")
        return None

# Command handler untuk memulai percakapan
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Please enter your email:")

# Fungsi untuk menangani pesan email dan meminta password
def handle_email(update: Update, context: CallbackContext):
    user_email = update.message.text  # Mendapatkan email dari pengguna
    context.user_data['email'] = user_email  # Menyimpan email dalam user_data
    update.message.reply_text("Please enter your password:")

# Fungsi untuk menangani password dan melakukan login
def handle_password(update: Update, context: CallbackContext):
    user_password = update.message.text  # Mendapatkan password dari pengguna
    user_email = context.user_data.get('email')  # Mendapatkan email yang sudah disimpan

    # Mengambil user_token dari GET request
    user_token = get_initial_data()

    if user_token:
        # Hash password menjadi MD5
        md5_password = md5_hash(user_password)
        # Melakukan login dengan mengirim POST request
        login_response = post_login_request(user_token, user_email, md5_password)

        if login_response:
            update.message.reply_text(f"Login successful! Response: {login_response}")
        else:
            update.message.reply_text("Login failed.")
    else:
        update.message.reply_text("Failed to retrieve user token. Try again later.")

# Main function untuk menjalankan bot
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Handler untuk /start command
    dispatcher.add_handler(CommandHandler("start", start))

    # Handler untuk email dan password
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_email, pass_user_data=True))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_password))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()