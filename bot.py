rom flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler, ConversationHandler
import logging
import time

app = Flask(__name__)

# Replace with your bot's token
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = Bot(8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M)
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Define Admins - Replace with real Telegram user IDs
ADMINS = [123456789, 987654321] # Add your admin Telegram user IDs here

# Database mock-up
trucks_at_well = []
staged_trucks = []
truck_data = {}

# Conversation states
TRUCK_NUMBER, CHASSIS_STATUS, LEAVE_WELL = range(3)

def is_admin(user_id):
    """Check if a user is an admin."""
    return user_id in ADMINS

def start(update, context):
    """Start the bot and request truck number."""
    update.message.reply_text("🚛 Welcome to *SandBot*! Please enter your *Truck Number*:")
    return TRUCK_NUMBER

def truck_number(update, context):
    """Store truck number and ask for chassis status with buttons."""
    truck_num = update.message.text
    context.user_data['truck_number'] = truck_num
    truck_data[truck_num] = {"status": "staged"}

    keyboard = [
        [InlineKeyboardButton("🛻 Chassis In", callback_data="chassis_in")],
        [InlineKeyboardButton("📦 Loaded", callback_data="loaded")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Select your truck status:", reply_markup=reply_markup)
    return CHASSIS_STATUS

def chassis_status(update, context):
    """Handle chassis status selection."""
    query = update.callback_query
    query.answer()
    truck_num = context.user_data['truck_number']
    status = query.data

    truck_data[truck_num]["status"] = status

    if status == "loaded":
        query.edit_message_text("✅ You are now *at the well*! Tap below when leaving:")
        trucks_at_well.append(truck_num)

        keyboard = [
            [InlineKeyboardButton("🏁 Leaving Well", callback_data="leaving_well")],
            [InlineKeyboardButton("🔄 Chassis Out", callback_data="chassis_out")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("Choose an option:", reply_markup=reply_markup)
    else:
        query.edit_message_text("✅ You are *staged* and will be called when needed.")
        staged_trucks.append(truck_num)

    return ConversationHandler.END

def leave_well(update, context):
    """Remove truck from the well when leaving."""
    query = update.callback_query
    query.answer()
    truck_num = context.user_data.get('truck_number')

    if truck_num in trucks_at_well:
        trucks_at_well.remove(truck_num)
        staged_trucks.append(truck_num)
        query.edit_message_text("✅ You have *left the well* and are now *staged* again.")
    return ConversationHandler.END

def status_update(update, context):
    """Show the current list of staged and well trucks with emojis."""
    well_list = "🚛 " + "\n🚛 ".join(trucks_at_well) if trucks_at_well else "None"
    staged_list = "📦 " + "\n📦 ".join(staged_trucks) if staged_trucks else "None"
    update.message.reply_text(f"*Current Status:*\n\n"
                              f"🔥 *Trucks at the Well:* \n{well_list}\n\n"
                              f"🅿️ *Staged Trucks:* \n{staged_list}")

def ai_chat_assist(update, context):
    """AI-powered response system for common driver questions."""
    message = update.message.text.lower()
    if "wait time" in message:
        wait_time_estimation(update, context)
    elif "where am i" in message:
        status_update(update, context)
    elif "help" in message:
        update.message.reply_text("🤖 *Commands:* /start, /status, /priority <truck_num>, /override <add/remove> <truck_num>, /wait_time")
    else:
        update.message.reply_text("💡 I'm here to assist. Try asking about *wait times* or *staging*.")

def admin_override(update, context):
    """Allow admins to manually add or remove trucks."""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        update.message.reply_text("❌ *Access Denied:* You are not an admin.")
        return

    if len(context.args) < 2:
        update.message.reply_text("⚠️ Usage: /override <add/remove> <truck_number>")
        return

    action = context.args[0].lower()
    truck_num = context.args[1]

    if action == "add":
        if truck_num not in staged_trucks:
            staged_trucks.append(truck_num)
            update.message.reply_text(f"✅ Truck {truck_num} *added to staging*.")
        else:
            update.message.reply_text("🚛 Truck is *already staged*.")

    elif action == "remove":
        if truck_num in staged_trucks:
            staged_trucks.remove(truck_num)
            update.message.reply_text(f"🗑️ Truck {truck_num} *removed from staging*.")
        elif truck_num in trucks_at_well:
            trucks_at_well.remove(truck_num)
            update.message.reply_text(f"🗑️ Truck {truck_num} *removed from the well*.")
        else:
            update.message.reply_text("❓ Truck not found.")

# Conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        TRUCK_NUMBER: [MessageHandler(Filters.text & ~Filters.command, truck_number)],
        CHASSIS_STATUS: [CallbackQueryHandler(chassis_status)],
        LEAVE_WELL: [CallbackQueryHandler(leave_well)]
    },
    fallbacks=[]
)

# Add handlers
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(CommandHandler("status", status_update))
dispatcher.add_handler(CommandHandler("override", admin_override, pass_args=True))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, ai_chat_assist))

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def respond():
    update = Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return 'ok'

if __name__ == '__main__':
    app.run(port=8443)
