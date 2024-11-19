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
