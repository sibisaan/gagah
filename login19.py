import logging
import httpx
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from urllib.parse import parse_qs

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# State constants for conversation
ROLEID, ZONEID, ACCOUNT, PASSWORD = range(4)

# Define global variables to store user data
user_data = {}

# Function to get fingerprint (fp) from a GET request
async def get_fingerprint():
    async with httpx.AsyncClient() as client:
        url = "https://mtacc.mobilelegends.com/v2.1/inapp/login-new"
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': 'userId=884785129; userGroup=12508',
            'Host': 'mtacc.mobilelegends.com',
            'Referer': 'https://mtacc.mobilelegends.com/v2.1/',
            'sec-ch-ua': '"Chromium";v="130", "Android WebView";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
            'X-Requested-With': 'com.mobile.legends',
        }
        response = await client.get(url, headers=headers)
        
        if response.status_code == 200:
            # Parse the URL-encoded response
            data = parse_qs(response.text)
            fingerprint = data.get('fp', [None])[0]  # Get fp from response, if exists
            return fingerprint
        else:
            logger.error(f"Failed to get fingerprint, status code: {response.status_code}")
            return None

# Command handler to start the bot and ask for roleid
async def start(update: Update, context: CallbackContext) -> int:
    user_data[update.message.chat_id] = {}  # Store user data per chat_id
    # Get fingerprint from server
    fp = await get_fingerprint()
    
    if not fp:
        await update.effective_message.reply("Gagal mendapatkan fingerprint. Coba lagi.")
        return ConversationHandler.END
    
    # Store fingerprint for future use
    user_data[update.message.chat_id]['fp'] = fp
    
    # Ask for Role ID
    await update.effective_message.reply("Masukkan Role ID Anda:")
    return ROLEID

# Handle user input for Role ID
async def roleid(update: Update, context: CallbackContext) -> int:
    user_data[update.message.chat_id]['roleid'] = update.message.text
    await update.effective_message.reply("Masukkan Zone ID Anda:")
    return ZONEID

# Handle user input for Zone ID
async def zoneid(update: Update, context: CallbackContext) -> int:
    user_data[update.message.chat_id]['zoneid'] = update.message.text
    await update.effective_message.reply("Masukkan Email Anda:")
    return ACCOUNT

# Handle user input for Account (Email)
async def account(update: Update, context: CallbackContext) -> int:
    user_data[update.message.chat_id]['account'] = update.message.text
    await update.effective_message.reply("Masukkan Password Anda:")
    return PASSWORD

# Handle user input for Password
async def password(update: Update, context: CallbackContext) -> int:
    user_data[update.message.chat_id]['password'] = update.message.text
    await update.effective_message.reply("Mempersiapkan login...")

    # Prepare the payload
    payload = {
        'roleid': user_data[update.message.chat_id]['roleid'],
        'zoneid': user_data[update.message.chat_id]['zoneid'],
        'account': user_data[update.message.chat_id]['account'],
        'password': user_data[update.message.chat_id]['password'],  # MD5 will be handled here later if needed
        'fp': user_data[update.message.chat_id]['fp'],
    }
    
    # Send login request to the server
    async with httpx.AsyncClient() as client:
        url = "https://api.mobilelegends.com/r"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; 220333QAG Build/RKQ1.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.107 Mobile Safari/537.36',
            'X-Requested-With': 'com.mobile.legends',
        }
        response = await client.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            # Parse the URL-encoded response
            response_data = parse_qs(response.text)
            await update.effective_message.reply(f"Login berhasil: {response_data}")
        else:
            await update.effective_message.reply("Login gagal, coba lagi.")
    
    return ConversationHandler.END

# Function to handle cancel action
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.effective_message.reply("Proses login dibatalkan.")
    return ConversationHandler.END

# Main function to setup the bot
def main():
    # Create the application
    application = Application.builder().token('7710828121:AAGdQmVhqQTFquxqwJ00BL_h_-vnWZ21ltw').build()

    # Define conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ROLEID: [MessageHandler(filters.TEXT & ~filters.COMMAND, roleid)],
            ZONEID: [MessageHandler(filters.TEXT & ~filters.COMMAND, zoneid)],
            ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, account)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Add conversation handler to the application
    application.add_handler(conversation_handler)

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
