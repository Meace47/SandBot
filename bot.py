from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import speech_recognition as sr
import os

# Data Storage
staged_trucks = {"100": [], "4070": []}
well_trucks = []
max_well_capacity = 5
allowed_4070s = 0  # Number of 4070s allowed at the well
stop_trucks = False
admin_roles = {
    "main_admins": ["5767285152,7116154394"],  # Full control
    "dispatchers": ["dispatcher_username"],  # Can move trucks
    "supervisors": ["supervisor_username"]  # Can only view status
}

def is_admin(update: Update, role: str) -> bool:
    return update.effective_user.username in admin_roles.get(role, [])

async def send_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows admin controls for eligible admins."""
    if is_admin(update, "main_admins") or is_admin(update, "dispatchers"):
        keyboard = [
            [InlineKeyboardButton("🚫 Stop Well", callback_data="stop"),
             InlineKeyboardButton("✅ Resume Well", callback_data="resume")],
            [InlineKeyboardButton("Set 4070 Slots", callback_data="set_4070")],
            [InlineKeyboardButton("📊 Status", callback_data="status")]
        ]
        await update.message.reply_text("⚙️ **Admin Controls:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command or when the bot is first opened."""
    await send_admin_menu(update, context)
    await send_main_menu(update, context)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main menu (buttons for selecting truck type and status)."""
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("🚛 4070", callback_data="4070"),
         InlineKeyboardButton("🔶 100", callback_data="100"),
         InlineKeyboardButton("🟢 Chassis In (CI)", callback_data="CI")]
    ]
    await update.message.reply_text("🚛 Welcome to SandBot! Select your truck type or check the current status.", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def stage_truck(update: Update, context: ContextTypes.DEFAULT_TYPE, truck_type: str):
    """Handles staging trucks when drivers select 4070, 100, or CI."""
    query = update.callback_query
    username = query.from_user.username

    truck_number = len(staged_trucks[truck_type]) + 1
    staged_trucks[truck_type].append(f"{truck_type}-{truck_number} ({username})")

    await query.edit_message_text(text=f"✅ **{username}** is staged as **{truck_type}-{truck_number}**.")
    await send_status_update(context)

async def send_status_update(context: ContextTypes.DEFAULT_TYPE):
    """Automatically sends updates when staging or well changes."""
    staging_list = "\n".join([f"🚏 {truck}" for truck in staged_trucks["100"] + staged_trucks["4070"]]) or "📭 No trucks staged."
    well_list = "\n".join([f"🏗 {truck}" for truck in well_trucks]) or "🏗 No trucks at the well."
    
    message = f"📊 **Current Status:**\n\n**🚏 Staging List:**\n{staging_list}\n\n**⛽ Well List:**\n{well_list}"
    for admin in admin_roles["main_admins"] + admin_roles["dispatchers"] + admin_roles["supervisors"]:
        try:
            await context.bot.send_message(chat_id=admin, text=message)
        except:
            pass

async def process_voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes voice commands for admin controls."""
    if update.message.voice and is_admin(update, "main_admins"):
        file = await context.bot.get_file(update.message.voice.file_id)
        file_path = "voice_command.ogg"
        await file.download(file_path)

        recognizer = sr.Recognizer()
        os.system(f"ffmpeg -i {file_path} voice_command.wav -y")

        with sr.AudioFile("voice_command.wav") as source:
            audio = recognizer.record(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            if "stop well" in command:
                await stop_trucks_command(update, context)
            elif "resume well" in command:
                await resume_trucks_command(update, context)
            elif "call next truck" in command:
                await call_to_well(update, context)
        except:
            await update.message.reply_text("⚠️ Could not recognize command.")

async def call_to_well(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Moves the next truck to the well if space is available."""
    global well_trucks

    if stop_trucks or len(well_trucks) >= max_well_capacity:
        return

    if staged_trucks["100"]:
        next_truck = staged_trucks["100"].pop(0)
        well_trucks.append(next_truck)
        await send_status_update(context)

async def stop_trucks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops well operations."""
    global stop_trucks
    stop_trucks = True
    await send_status_update(context)

async def resume_trucks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resumes well operations."""
    global stop_trucks
    stop_trucks = False
    await send_status_update(context)

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the admin control menu."""
    keyboard = [
        [InlineKeyboardButton("🚫 Stop Well", callback_data="stop"),
         InlineKeyboardButton("✅ Resume Well", callback_data="resume")],
        [InlineKeyboardButton("Set 4070 Slots", callback_data="set_4070")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ]
    await update.callback_query.edit_message_text("⚙️ **Admin Controls:**", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    """Starts the bot application."""
    app = ApplicationBuilder().token("8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_voice_command))
    app.add_handler(MessageHandler(filters.VOICE, process_voice_command))
    app.add_handler(CallbackQueryHandler(stage_truck, pattern="^(4070|100|CI)$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
