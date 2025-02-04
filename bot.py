from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

# Data Storage
staged_trucks = {}
well_trucks = []
max_well_capacity = 5
stop_trucks = False  # Control truck movement
admin_list = ["admin_username"]  # Replace with actual admin usernames

# Admin Commands Description
admin_commands = {
    "/stop": "Stops all trucks from coming to the well.",
    "/resume": "Allows trucks to go to the well again.",
    "/setmax [number]": "Changes the maximum number of trucks allowed at the well.",
    "/commands": "Shows this list of admin commands."
}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to SandBot! Use the menu to choose your status.", reply_markup=get_truck_options())

def is_admin(update):
    return update.message.from_user.username in admin_list

def stop_trucks_command(update: Update, context: CallbackContext):
    global stop_trucks
    if is_admin(update):
        stop_trucks = True
        update.message.reply_text("🚫 Trucks are now stopped from coming to the well. All will be staged.")
    else:
        update.message.reply_text("⚠️ You are not authorized to use this command.")

def resume_trucks_command(update: Update, context: CallbackContext):
    global stop_trucks
    if is_admin(update):
        stop_trucks = False
        update.message.reply_text("✅ Trucks can now go to the well again.")
    else:
        update.message.reply_text("⚠️ You are not authorized to use this command.")

def set_max_well(update: Update, context: CallbackContext):
    global max_well_capacity
    if is_admin(update):
        try:
            new_capacity = int(context.args[0])
            max_well_capacity = new_capacity
            update.message.reply_text(f"✅ Well capacity set to {new_capacity} trucks.")
        except (IndexError, ValueError):
            update.message.reply_text("⚠️ Usage: /setmax [number]")
    else:
        update.message.reply_text("⚠️ You are not authorized to use this command.")

def show_admin_commands(update: Update, context: CallbackContext):
    if is_admin(update):
        commands_text = "\n".join([f"{cmd}: {desc}" for cmd, desc in admin_commands.items()])
        update.message.reply_text(f"📋 **Admin Commands:**\n{commands_text}")
    else:
        update.message.reply_text("⚠️ You are not authorized to view admin commands.")

def get_truck_options():
    keyboard = [
        [InlineKeyboardButton("4070", callback_data="4070"),
         InlineKeyboardButton("100", callback_data="100"),
         InlineKeyboardButton("Chassis In (CI)", callback_data="CI")]
    ]
    return InlineKeyboardMarkup(keyboard)

def truck_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    truck_type = query.data
    username = query.from_user.username
    query.answer()

    if truck_type == "CI":
        staged_trucks[username] = f"{truck_type}"
        query.edit_message_text(text=f"✅ You are staged as **{truck_type}**.")
    else:
        # If not Chassis In, ask if they are Chassis Out
        keyboard = [
            [InlineKeyboardButton("Yes, Chassis Out (CO)", callback_data=f"{truck_type}-CO"),
             InlineKeyboardButton("No", callback_data=truck_type)]
        ]
        query.edit_message_text(text="Are you Chassis Out (CO)?", reply_markup=InlineKeyboardMarkup(keyboard))

def chassis_out_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    truck_status = query.data
    username = query.from_user.username
    query.answer()

    staged_trucks[username] = f"{truck_status}"
    query.edit_message_text(text=f"✅ You are staged as **{truck_status}**.")

def call_to_well(update: Update, context: CallbackContext):
    if is_admin(update):
        if len(well_trucks) >= max_well_capacity:
            update.message.reply_text("🚧 The well is full! No more trucks can enter.")
            return
        
        if not staged_trucks:
            update.message.reply_text("📭 No trucks are currently staged.")
            return
        
        # Move the first staged truck to the well
        username, truck_status = staged_trucks.popitem()
        keyboard = [
            [InlineKeyboardButton("✅ On the Way", callback_data=f"confirm_{username}_{truck_status}"),
             InlineKeyboardButton("❌ Not Available", callback_data=f"cancel_{username}")]
        ]
        update.message.reply_text(f"🚛 {username}, you've been called to the well!\nConfirm your status:", 
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text("⚠️ You are not authorized to call trucks to the well.")

def confirm_well_status(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("_")
    action = data[0]
    username = data[1]
    truck_status = data[2]
    query.answer()

    if action == "confirm":
        well_trucks.append(f"{username} - {truck_status}")
        query.edit_message_text(text=f"✅ {username} is now at the well as **{truck_status}**.")
    elif action == "cancel":
        query.edit_message_text(text=f"❌ {username} is not available and has been removed from staging.")

def main():
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    dp = updater.dispatcher

    # Command Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop_trucks_command))
    dp.add_handler(CommandHandler("resume", resume_trucks_command))
    dp.add_handler(CommandHandler("setmax", set_max_well, pass_args=True))
    dp.add_handler(CommandHandler("commands", show_admin_commands))
    dp.add_handler(CommandHandler("callwell", call_to_well))  # Admins call trucks

    # Callback Query Handlers
    dp.add_handler(CallbackQueryHandler(truck_selection, pattern="^(4070|100|CI)$"))
    dp.add_handler(CallbackQueryHandler(chassis_out_selection, pattern="^(4070-CO|100-CO|4070|100)$"))
    dp.add_handler(CallbackQueryHandler(confirm_well_status, pattern="^(confirm|cancel)_.*"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
