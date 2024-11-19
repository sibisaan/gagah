import hashlib
import aiohttp  # Menggunakan aiohttp untuk request HTTP asinkron
from telegram import Update  # Pastikan Update diimpor
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackContext  # CallbackContext juga diimpor
from telegram.ext.filters import Text

# Token Telegram Bot Anda
TELEGRAM_API_TOKEN = '7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw'

# URL API Mobile Legends untuk login
LOGIN_URL = 'https://accountmtapi.mobilelegends.com/'

# Stages untuk ConversationHandler
ID, SERVER, EMAIL, PASSWORD = range(4)

# Fungsi untuk meng-hash password menggunakan MD5
def md5_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

# Fungsi untuk menghasilkan sign
def generate_sign(data: dict, secret_key: str = "secret_key") -> str:
    """
    Fungsi untuk menghasilkan tanda tangan (sign) berdasarkan data dan secret key.
    """
    # Concatenate semua parameter dalam urutan tertentu
    sign_string = ''.join([str(value) for key, value in sorted(data.items())])
    sign_string += secret_key  # Tambahkan secret key di akhir
    return hashlib.md5(sign_string.encode()).hexdigest()

# Fungsi untuk mendapatkan game_token (misalnya dari login pertama)
async def get_game_token(account: str) -> str:
    """
    Fungsi untuk mendapatkan game_token yang valid dari API Mobile Legends.
    Anda harus mengganti ini dengan mekanisme yang benar untuk mendapatkan game_token.
    """
    # Simulasi pengambilan game_token (misalnya, dari API atau pengaturan sebelumnya)
    return hashlib.md5(account.encode()).hexdigest()  # Contoh sederhana

# Fungsi untuk login ke Mobile Legends API (menggunakan aiohttp)
async def login_to_mobile_legends(froleid, fzoneid, account, md5pwd):
    """
    Fungsi untuk mengirimkan data login ke API Mobile Legends secara asinkron.
    """
    game_token = await get_game_token(account)  # Mendapatkan game_token yang valid
    sign = generate_sign({
        "account": account,
        "froleid": froleid,
        "fzoneid": fzoneid,
        "game_token": game_token
    })

    # Payload login
    data = {
        "op": "login",
        "sign": sign,
        "params": {
            "account": account,
            "md5pwd": md5pwd,
            "game_token": game_token,
            "recaptcha_token": "",
            "country": ""
        },
        "lang": "id",
        "froleid": froleid,   # ID Akun (froleid)
        "fzoneid": fzoneid    # Server Akun (zoneid)
    }

    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
        'X-Requested-With': 'com.mobile.legends',
    }

    # Mengirimkan POST request ke API dengan aiohttp
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(LOGIN_URL, json=data, headers=headers) as response:
                if response.status == 200:
                    # Cek apakah API mengembalikan status sukses
                    result = await response.json()
                    if result.get('code') == 0:  # Cek jika API mengembalikan code 0 (berhasil)
                        return result
                    else:
                        # API mengembalikan error meskipun status 200
                        return {"error": result.get('msg', 'Unknown error')}
                else:
                    # Tangani error HTTP selain 200
                    return {"error": f"HTTP Error {response.status}"}
        except aiohttp.ClientError as e:
            return {"error": f"Request failed: {str(e)}"}

# Handler untuk perintah /start
async def start(update: Update, context: CallbackContext) -> int:
    """
    Handler untuk perintah /start
    """
    await update.message.reply_text(
        'Selamat datang! Saya akan membantu Anda untuk login.\n\n' +
        '1. Masukkan ID Akun Anda (froleid)\n' +
        '2. Masukkan Server Akun Anda (fzoneid)\n' +
        '3. Masukkan Email (account)\n' +
        '4. Masukkan Password (md5pwd)'
    )
    return ID

# Menerima ID Akun
async def receive_account_id(update: Update, context: CallbackContext) -> int:
    """
    Menerima ID Akun dan melanjutkan ke input server (fzoneid)
    """
    context.user_data['froleid'] = update.message.text
    await update.message.reply_text('ID Akun diterima. Sekarang masukkan Server Akun (fzoneid) Anda.')
    return SERVER

# Menerima Server Akun
async def receive_server(update: Update, context: CallbackContext) -> int:
    """
    Menerima Server Akun (fzoneid) dan melanjutkan ke input email (account)
    """
    context.user_data['fzoneid'] = update.message.text
    await update.message.reply_text('Server diterima. Sekarang masukkan email Anda (account).')
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
    context.user_data['md5pwd'] = update.message.text  # Assume password already MD5 encoded

    # Mengambil data yang sudah dikumpulkan
    froleid = context.user_data['froleid']
    fzoneid = context.user_data['fzoneid']
    account = context.user_data['account']
    md5pwd = md5_hash(context.user_data['md5pwd'])  # Hash password jika perlu

    # Proses login
    result = await login_to_mobile_legends(froleid, fzoneid, account, md5pwd)

    if "error" in result:
        # Jika ada error dalam login, kirim pesan error ke pengguna
        await update.message.reply_text(f"Login gagal! Error: {result['error']}")
    else:
        # Jika login berhasil, tampilkan hasilnya
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
            ID: [MessageHandler(Text(), receive_account_id)],  # Ganti Filters menjadi Text()
            SERVER: [MessageHandler(Text(), receive_server)],
            EMAIL: [MessageHandler(Text(), receive_email)],
            PASSWORD: [MessageHandler(Text(), receive_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conversation_handler)

    # Mulai bot
    application.run_polling()

if __name__ == '__main__':
    main()
