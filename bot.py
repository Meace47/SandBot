from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Data Storage
staged_trucks = {}
well_trucks = []
max_well_capacity = 5
stop_trucks = False  # Controls truck movement
admin_list = ["5767285152"]  # Replace with actual admin usernames

def is_admin(update: Update) -> bool:
    return update.effective_user.username in admin_list

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the main menu (buttons for selecting truck type and status)."""
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("🚛 4070", callback_data="4070"),
         InlineKeyboardButton("🔶 100", callback_data="100"),
         InlineKeyboardButton("🟢 Chassis In (CI)", callback_data="CI")]
    ]
    if is_admin(update):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Commands", callback_data="admin_menu")])

    message_text = "🚛 Welcome to SandBot! Select your truck type or check the current status."
    
    # Prevent "Message is not modified" error
    try:
        await update.message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        pass  # Ignore duplicate errors

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command or when the bot is first opened."""
    await send_main_menu(update, context)

async def handle_new_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles any new messages and automatically shows the menu."""
    if update.message.text:  # Only respond to text messages
        await send_main_menu(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data == "status":
        await status_check(update, context)
    elif query.data == "admin_menu":
        await admin_menu(update, context)
    elif query.data == "stop":
        await stop_trucks_command(update, context)
    elif query.data == "resume":
        await resume_trucks_command(update, context)
    elif query.data == "call_well":
        await call_to_well(update, context)

async def status_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the current truck staging and well status."""
    staging_info = "\n".join([f"🚛 {u} - {s}" for u, s in staged_trucks.items()]) if staged_trucks else "📭 No trucks staged."
    well_info = "\n".join([f"🏗 {t}" for t in well_trucks]) if well_trucks else "🏗 No trucks at the well."
    status_text = f"📊 **Current Status:**\n\n**🚏 Staged Trucks:**\n{staging_info}\n\n**⛽ Well Trucks:**\n{well_info}\n\n**Max Capacity:** {max_well_capacity}\n**Well Status:** {'🚫 STOPPED' if stop_trucks else '✅ ACTIVE'}"

    try:
        await update.callback_query.edit_message_text(text=status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 Refresh Status", callback_data="status")]]))
    except:
        pass  # Ignore errors when message content is unchanged

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the admin control menu."""
    keyboard = [
        [InlineKeyboardButton("🚫 Stop Well", callback_data="stop"),
         InlineKeyboardButton("✅ Resume Well", callback_data="resume")],
        [InlineKeyboardButton("🚛 Call Next Truck", callback_data="call_well")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ]
    await update.callback_query.edit_message_text("⚙️ **Admin Commands:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def stop_trucks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops trucks from going to the well."""
    global stop_trucks
    if is_admin(update):
        stop_trucks = True
        await send_admin_update(context, "🚫 **STOP ISSUED** - No more trucks can enter the well. All will be staged.")

async def resume_trucks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resumes truck movement to the well."""
    global stop_trucks
    if is_admin(update):
        stop_trucks = False
        await send_admin_update(context, "✅ **RESUME ISSUED** - Trucks can now go to the well again.")

async def call_to_well(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calls the next staged truck to the well."""
    if is_admin(update):
        if len(well_trucks) >= max_well_capacity:
            await update.message.reply_text("🚧 The well is full! No more trucks can enter.")
            return
        
        if not staged_trucks:
            await update.message.reply_text("📭 No trucks are currently staged.")
            return
        
        username, truck_status = staged_trucks.popitem()
        keyboard = [
            [InlineKeyboardButton("✅ On the Way", callback_data=f"confirm_{username}_{truck_status}"),
             InlineKeyboardButton("❌ Not Available", callback_data=f"cancel_{username}")]
        ]
        await update.message.reply_text(f"🚛 **{username}**, you've been called to the well!\nConfirm your status:", 
                                        reply_markup=InlineKeyboardMarkup(keyboard))
        await send_admin_update(context, f"📢 **{username}** has been called to the well!")

async def send_admin_update(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Sends an update to all admins."""
    for admin in admin_list:
        try:
            await context.bot.send_message(chat_id=admin, text=message)
        except:
            pass  # Ignore errors (e.g., bot is not in a chat with the admin)

def main():
    """Starts the bot application."""
    app = ApplicationBuilder().token("8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_messages))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
