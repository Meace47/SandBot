from telegram.ext import Updater, CommandHandler

def start(update, context):
    update.message.reply_text("Hello! SandBot is now active.")

def main():
    # Replace 'YOUR_API_TOKEN' with your actual Telegram bot token
    updater = Updater("8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()