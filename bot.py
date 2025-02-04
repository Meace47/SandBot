from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Data Storage
staged_trucks = {"100": [], "4070": []}
well_trucks = []
max_well_capacity = 5
allowed_4070s = 0  # Number of 4070s allowed at the well
stop_trucks = False
admin_list = ["5767285152,7116154394"]  # Replace with actual admin usernames

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
        keyboard.append([InlineKeyboardButton("⚙️ Admin Controls", callback_data="admin_menu")])

    await update.message.reply_text("🚛 Welcome to SandBot! Select your truck type or check the current status.", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command or when the bot is first opened."""
    await send_main_menu(update, context)

async def handle_new_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles any new messages and automatically shows the menu."""
    if update.message.text:
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
    elif query.data == "set_4070":
        await set_4070_slots(update, context)
    elif query.data in ["4070", "100", "CI"]:
        await stage_truck(update, context, query.data)
    elif query.data.startswith("leaving_"):
        await leaving_well(update, context, query.data)

async def stage_truck(update: Update, context: ContextTypes.DEFAULT_TYPE, truck_type: str):
    """Handles staging trucks when drivers select 4070, 100, or CI."""
    query = update.callback_query
    username = query.from_user.username

    if truck_type == "CI":
        await query.edit_message_text(text=f"✅ **{username}** is staged as **{truck_type}**.")
        await send_admin_update(context, f"🚛 **{username}** is staged as **{truck_type}**.")
    else:
        staged_trucks[truck_type].append(username)
        await query.edit_message_text(text=f"✅ **{username}** is staged as **{truck_type}**.")
        await send_admin_update(context, f"🚛 **{username}** is staged as **{truck_type}**.")

    await check_well_status(context)

async def check_well_status(context: ContextTypes.DEFAULT_TYPE):
    """Automatically fills the well with the next 100 when space opens up."""
    global well_trucks

    if stop_trucks or len(well_trucks) >= max_well_capacity:
        return  # Stop auto-filling if well is full or stopped

    # Fill well with 100s first
    while len(well_trucks) < max_well_capacity and staged_trucks["100"]:
        next_truck = staged_trucks["100"].pop(0)
        well_trucks.append(next_truck)
        await send_admin_update(context, f"✅ **{next_truck}** moved to the well.")

    # Allow 4070s only if admins have set a slot
    while len(well_trucks) < max_well_capacity and allowed_4070s > 0 and staged_trucks["4070"]:
        next_truck = staged_trucks["4070"].pop(0)
        well_trucks.append(next_truck)
        allowed_4070s -= 1
        await send_admin_update(context, f"✅ **{next_truck}** moved to the well (4070 slot used).")

async def leaving_well(update: Update, context: ContextTypes.DEFAULT_TYPE, leave_type: str):
    """Handles when a driver leaves the well."""
    query = update.callback_query
    username = query.from_user.username

    if username in well_trucks:
        well_trucks.remove(username)
        
        if leave_type == "leaving_empty":
            leave_status = "Leaving Well - Empty (LW-E)"
        elif leave_type == "leaving_co":
            leave_status = "Leaving Well - Chassis Out (LW-CO)"
        else:
            return
        
        await query.edit_message_text(text=f"🚛 **{username}** has left the well as **{leave_status}**.")
        await send_admin_update(context, f"🚛 **{username}** has left the well as **{leave_status}**.")
        await check_well_status(context)  # Move next truck when one leaves

async def set_4070_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows admins to set the number of 4070s that can be at the well."""
    global allowed_4070s
    query = update.callback_query

    # Example: Admins can set 1-3 slots for 4070s
    keyboard = [[InlineKeyboardButton(str(i), callback_data=f"allow_4070_{i}") for i in range(1, 4)]]
    await query.edit_message_text("📢 Select the number of 4070 slots allowed:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the admin control menu."""
    keyboard = [
        [InlineKeyboardButton("🚫 Stop Well", callback_data="stop"),
         InlineKeyboardButton("✅ Resume Well", callback_data="resume")],
        [InlineKeyboardButton("Set 4070 Slots", callback_data="set_4070")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ]
    await update.callback_query.edit_message_text("⚙️ **Admin Controls:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_admin_update(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Sends an update to all admins."""
    for admin in admin_list:
        try:
            await context.bot.send_message(chat_id=admin, text=message)
        except:
            pass  # Ignore errors

def main():
    """Starts the bot application."""
    app = ApplicationBuilder().token("8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_messages))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
