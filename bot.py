from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Data Storage
staged_trucks = {}
well_trucks = []
max_well_capacity = 5
stop_trucks = False  # Controls truck movement
admin_list = ["5767285152"]  # Replace with actual admin usernames

def is_admin(update: Update) -> bool:
    return update.effective_user.username in admin_list

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("🚛 4070", callback_data="4070"),
         InlineKeyboardButton("🔶 100", callback_data="100"),
         InlineKeyboardButton("🟢 Chassis In (CI)", callback_data="CI")]
    ]
    if is_admin(update):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Commands", callback_data="admin_menu")])

    await update.message.reply_text("Welcome to SandBot! Select your truck type or check the status:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    staging_info = "\n".join([f"🚛 {u} - {s}" for u, s in staged_trucks.items()]) if staged_trucks else "📭 No trucks staged."
    well_info = "\n".join([f"🏗 {t}" for t in well_trucks]) if well_trucks else "🏗 No trucks at the well."
    status_text = f"📊 **Current Status:**\n\n**🚏 Staged Trucks:**\n{staging_info}\n\n**⛽ Well Trucks:**\n{well_info}\n\n**Max Capacity:** {max_well_capacity}\n**Well Status:** {'🚫 STOPPED' if stop_trucks else '✅ ACTIVE'}"
    
    await update.callback_query.edit_message_text(text=status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 Refresh Status", callback_data="status")]]))

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚫 Stop Well", callback_data="stop"),
         InlineKeyboardButton("✅ Resume Well", callback_data="resume")],
        [InlineKeyboardButton("🚛 Call Next Truck", callback_data="call_well")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ]
    await update.callback_query.edit_message_text("⚙️ **Admin Commands:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def stop_trucks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stop_trucks
    if is_admin(update):
        stop_trucks = True
        await send_admin_update(context, "🚫 **STOP ISSUED** - No more trucks can enter the well. All will be staged.")
    else:
        await update.message.reply_text("⚠️ You are not authorized to use this command.")

async def resume_trucks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stop_trucks
    if is_admin(update):
        stop_trucks = False
        await send_admin_update(context, "✅ **RESUME ISSUED** - Trucks can now go to the well again.")
    else:
        await update.message.reply_text("⚠️ You are not authorized to use this command.")

async def call_to_well(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    for admin in admin_list:
        await context.bot.send_message(chat_id=admin, text=message)

def main():
    app = ApplicationBuilder().token("8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
