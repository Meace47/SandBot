from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# Data Storage
staged_trucks = {}
well_trucks = []
max_well_capacity = 5
stop_trucks = False  # Controls truck movement
admin_list = ["5767285152"]  # Replace with actual admin usernames

def is_admin(update):
    return update.effective_user.username in admin_list

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("🚛 4070", callback_data="4070"),
         InlineKeyboardButton("🔶 100", callback_data="100"),
         InlineKeyboardButton("🟢 Chassis In (CI)", callback_data="CI")]
    ]
    if is_admin(update):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Commands", callback_data="admin_menu")])
    
    update.message.reply_text("Welcome to SandBot! Select your truck type or check the status:", 
                              reply_markup=InlineKeyboardMarkup(keyboard))

def truck_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    truck_type = query.data
    username = query.from_user.username
    query.answer()

    if truck_type == "CI":
        staged_trucks[username] = "CI"
    else:
        keyboard = [
            [InlineKeyboardButton("Yes, Chassis Out (CO)", callback_data=f"{truck_type}-CO"),
             InlineKeyboardButton("No", callback_data=truck_type)]
        ]
        query.edit_message_text(text="Are you Chassis Out (CO)?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    query.edit_message_text(text=f"✅ You are staged as **{truck_type}**.")
    send_admin_update(f"🚛 **{username}** is staged as **{truck_type}**.")

def chassis_out_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    truck_status = query.data
    username = query.from_user.username
    query.answer()

    staged_trucks[username] = truck_status
    query.edit_message_text(text=f"✅ You are staged as **{truck_status}**.")
    send_admin_update(f"🚛 **{username}** is staged as **{truck_status}**.")

def call_to_well(update: Update, context: CallbackContext):
    if is_admin(update):
        if len(well_trucks) >= max_well_capacity:
            update.message.reply_text("🚧 The well is full! No more trucks can enter.")
            return
        
        if not staged_trucks:
            update.message.reply_text("📭 No trucks are currently staged.")
            return
        
        username, truck_status = staged_trucks.popitem()
        keyboard = [
            [InlineKeyboardButton("✅ On the Way", callback_data=f"confirm_{username}_{truck_status}"),
             InlineKeyboardButton("❌ Not Available", callback_data=f"cancel_{username}")]
        ]
        update.message.reply_text(f"🚛 **{username}**, you've been called to the well!\nConfirm your status:", 
                                  reply_markup=InlineKeyboardMarkup(keyboard))
        send_admin_update(f"📢 **{username}** has been called to the well!")

def confirm_well_status(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("_")
    action = data[0]
    username = data[1]
    truck_status = data[2] if len(data) > 2 else None
    query.answer()

    if action == "confirm":
        well_trucks.append(f"{username} - {truck_status}")
        query.edit_message_text(text=f"✅ {username} is now at the well as **{truck_status}**.")
        send_admin_update(f"🚛 **{username}** is now at the well as **{truck_status}**.")
    elif action == "cancel":
        query.edit_message_text(text=f"❌ {username} is not available and has been removed from staging.")
        send_admin_update(f"🚫 **{username}** was called but is **not available**.")

def stop_trucks_command(update: Update, context: CallbackContext):
    global stop_trucks
    if is_admin(update):
        stop_trucks = True
        send_admin_update("🚫 **STOP ISSUED** - No more trucks can enter the well. All will be staged.")
    else:
        update.message.reply_text("⚠️ You are not authorized to use this command.")

def resume_trucks_command(update: Update, context: CallbackContext):
    global stop_trucks
    if is_admin(update):
        stop_trucks = False
        send_admin_update("✅ **RESUME ISSUED** - Trucks can now go to the well again.")
    else:
        update.message.reply_text("⚠️ You are not authorized to use this command.")

def set_max_well(update: Update, context: CallbackContext):
    global max_well_capacity
    if is_admin(update):
        try:
            new_capacity = int(update.message.text.split()[1])
            max_well_capacity = new_capacity
            send_admin_update(f"🔧 **Max well capacity set to {new_capacity} trucks.**")
        except (IndexError, ValueError):
            update.message.reply_text("⚠️ Usage: /setmax [number]")
    else:
        update.message.reply_text("⚠️ You are not authorized to use this command.")

def send_admin_update(message):
    for admin in admin_list:
        context.bot.send_message(chat_id=admin, text=message)

def status_check(update: Update, context: CallbackContext):
    staging_info = "\n".join([f"🚛 {u} - {s}" for u, s in staged_trucks.items()]) if staged_trucks else "📭 No trucks staged."
    well_info = "\n".join([f"🏗 {t}" for t in well_trucks]) if well_trucks else "🏗 No trucks at the well."
    status_text = f"📊 **Current Status:**\n\n**🚏 Staged Trucks:**\n{staging_info}\n\n**⛽ Well Trucks:**\n{well_info}\n\n**Max Capacity:** {max_well_capacity}\n**Well Status:** {'🚫 STOPPED' if stop_trucks else '✅ ACTIVE'}"
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=status_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 Refresh Status", callback_data="status")]]))

def admin_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🚫 Stop Well", callback_data="stop"),
         InlineKeyboardButton("✅ Resume Well", callback_data="resume")],
        [InlineKeyboardButton("🚛 Call Next Truck", callback_data="call_well")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ]
    update.callback_query.answer()
    update.callback_query.edit_message_text("⚙️ **Admin Commands:**", reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "status":
        status_check(update, context)
    elif query.data == "admin_menu":
        admin_menu(update, context)
    elif query.data == "stop":
        stop_trucks_command(update, context)
    elif query.data == "resume":
        resume_trucks_command(update, context)
    elif query.data == "call_well":
        call_to_well(update, context)

def main():
    updater = Updater("8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
