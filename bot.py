from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Start command function
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! SandBot is now active.")

# Main function to run the bot
def main():
    # Replace 'YOUR_API_TOKEN' with your actual bot token
    application = Application.builder().token("8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M").build()

    # Add command handler
    application.add_handler(CommandHandler("start", start))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
