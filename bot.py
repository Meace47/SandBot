import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = "8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M"

# Truck staging and well management
staging_data = {"4070": [], "100": [], "well": []}
WELL_LIMIT = 5
admin_ids = [5767285152, 7116154394]  # Admin Telegram IDs

# Function to display truck options
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚛 4070", callback_data="4070")],
        [InlineKeyboardButton("🚚 100", callback_data="100")],
        [InlineKeyboardButton("📊 View Status", callback_data="view_status")]  # Always visible
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose your truck type or view the current status:", reply_markup=reply_markup)
    
# Function to handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    truck_type = query.data

    if truck_type == "view_status":
        await view_status(update, context)
    elif truck_type == "refresh_status":
        await refresh_status(update, context)
    elif truck_type in ["4070", "100"]:
        keyboard = [
            [InlineKeyboardButton("🛑 Yes, Chassis Out", callback_data=f"chassis_out_{truck_type}")],
            [InlineKeyboardButton("❌ No, Just Stage", callback_data=f"stage_{truck_type}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
            [InlineKeyboardButton("📊 View Status", callback_data="view_status")]  # Always visible
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"You selected {truck_type}. Do you want to Chassis Out?", reply_markup=reply_markup)

    elif truck_type.startswith("chassis_out_"):
        _, selected_type = truck_type.split("_", 1)
        await process_chassis_out(query, selected_type, user_id, context)

    elif truck_type.startswith("stage_"):
        _, selected_type = truck_type.split("_", 1)
        await process_staging(query, selected_type, user_id, context)

    elif truck_type == "leave_well":
        await process_leave_well(query, user_id, context)

    elif truck_type == "back":
        await start(update, context)

# Function to display truck status in real time
async def view_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    well_status = "🟢 Running" if len(staging_data["well"]) > 0 else "🔴 Down"
    
    msg = "📊 **Current Trucking Status:**\n\n"
    msg += f"🛢️ **Well Status:** {well_status}\n"
    msg += f"🚛 **Trucks at the Well:** {len(staging_data['well'])}/{WELL_LIMIT}\n"
    msg += f"🟠 **4070 Trucks Staged:** {len(staging_data['4070'])}\n"
    msg += f"🟢 **100 Mesh Trucks Staged:** {len(staging_data['100'])}\n"

    keyboard = [[InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_status")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, reply_markup=reply_markup)

# Function to handle refreshing the status view
async def refresh_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    well_status = "🟢 Running" if len(staging_data["well"]) > 0 else "🔴 Down"

    msg = "📊 **Updated Trucking Status:**\n\n"
    msg += f"🛢️ **Well Status:** {well_status}\n"
    msg += f"🚛 **Trucks at the Well:** {len(staging_data['well'])}/{WELL_LIMIT}\n"
    msg += f"🟠 **4070 Trucks Staged:** {len(staging_data['4070'])}\n"
    msg += f"🟢 **100 Mesh Trucks Staged:** {len(staging_data['100'])}\n"

keyboard = [
    [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_status")],
    [InlineKeyboardButton("⬅️ Back", callback_data="back")],
    [InlineKeyboardButton("📊 View Status", callback_data="view_status")]  # Always available
]
reply_markup = InlineKeyboardMarkup(keyboard)

await query.edit_message_text(msg, reply_markup=reply_markup)

# Function to process chassis out
async def process_chassis_out(query, truck_type, user_id, context):
    truck_entry = f"{user_id} (CO)"  # Mark with CO

    if len(staging_data["well"]) < WELL_LIMIT:
        staging_data["well"].append(truck_entry)
        await query.edit_message_text(f"✅ You have been sent to the well as {truck_type} (CO).")
    else:
        staging_data[truck_type].append(truck_entry)
        await query.edit_message_text(f"🚧 Well is full. You are staged as {truck_type} (CO).")

# Function to process staging (if user chooses not to chassis out)
async def process_staging(query, truck_type, user_id, context):
    truck_entry = f"{user_id}"  # No CO tag for normal staging

    if len(staging_data["well"]) < WELL_LIMIT:
        staging_data["well"].append(truck_entry)
        await query.edit_message_text(f"✅ You have been sent to the well as {truck_type}.")
    else:
        staging_data[truck_type].append(truck_entry)
        await query.edit_message_text(f"🚧 Well is full. You are staged as {truck_type}.")

# Function to process leaving the well
async def process_leave_well(query, user_id, context):
    for i, truck in enumerate(staging_data["well"]):
        if str(user_id) in truck:
            staging_data["well"].pop(i)
            await query.edit_message_text("✅ You have left the well.")
            await move_next_to_well(context)
            return

    await query.edit_message_text("⚠️ You are not at the well.")

# Function to move the next truck to the well automatically
async def move_next_to_well(context):
    if len(staging_data["well"]) < WELL_LIMIT:
        if staging_data["100"]:
            next_truck = staging_data["100"].pop(0)
            staging_data["well"].append(next_truck)
        elif staging_data["4070"]:
            next_truck = staging_data["4070"].pop(0)
            staging_data["well"].append(next_truck)

# Function to display staging info with numbered trucks
async def staging_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📋 **Staging Information:**\n\n"

    msg += "**WELL:**\n"
    if staging_data["well"]:
        for i, truck in enumerate(staging_data["well"], 1):
            msg += f"🔵 #{i}: Truck {truck}\n"
    else:
        msg += "🔵 No trucks at the well.\n"

    msg += "\n**100 Mesh Staging:**\n"
    if staging_data["100"]:
        for i, truck in enumerate(staging_data["100"], 1):
            msg += f"🟢 #{i}: Truck {truck}\n"
    else:
        msg += "🟢 No trucks staged.\n"

    msg += "\n**4070 Staging:**\n"
    if staging_data["4070"]:
        for i, truck in enumerate(staging_data["4070"], 1):
            msg += f"🟠 #{i}: Truck {truck}\n"
    else:
        msg += "🟠 No trucks staged.\n"

    await update.message.reply_text(msg)

# Admin function to manually add a truck to the well
async def add_well(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in admin_ids:
        truck_num = int(context.args[0]) if context.args else None
        truck_list = staging_data["100"] + staging_data["4070"]
        
        if 0 < truck_num <= len(truck_list):
            selected_truck = truck_list[truck_num - 1]
            if len(staging_data["well"]) < WELL_LIMIT:
                staging_data["well"].append(selected_truck)
                await update.message.reply_text(f"✅ Truck #{truck_num} added to the well.")
            else:
                await update.message.reply_text("🚧 Well is full!")
        else:
            await update.message.reply_text("⚠️ Invalid truck number.")
    else:
        await update.message.reply_text("❌ You are not an admin.")

# Function to display staging info with numbers
async def staging_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📋 **Staging Information:**\n\n"

    msg += "**WELL:**\n"
    if staging_data["well"]:
        for i, truck in enumerate(staging_data["well"], 1):
            msg += f"🔵 #{i}: Truck {truck}\n"
    else:
        msg += "🔵 No trucks at the well.\n"

    msg += "\n**100 Mesh Staging:**\n"
    if staging_data["100"]:
        for i, truck in enumerate(staging_data["100"], 1):
            msg += f"🟢 #{i}: Truck {truck}\n"
    else:
        msg += "🟢 No trucks staged.\n"

    msg += "\n**4070 Staging:**\n"
    if staging_data["4070"]:
        for i, truck in enumerate(staging_data["4070"], 1):
            msg += f"🟠 #{i}: Truck {truck}\n"
    else:
        msg += "🟠 No trucks staged.\n"

    await update.message.reply_text(msg)

# Admin function to manually remove a truck from the well
async def remove_well(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in admin_ids:
        truck_num = int(context.args[0]) if context.args else None
        
        if 0 < truck_num <= len(staging_data["well"]):
            removed_truck = staging_data["well"].pop(truck_num - 1)
            await update.message.reply_text(f"ðŸš› Truck #{truck_num} removed from the well.")
            await move_next_to_well(context)
        else:
            await update.message.reply_text("âš ï¸ Invalid truck number.")
    else:
        await update.message.reply_text("âŒ You are not an admin.")

# Admin function to clear staging
async def clear_staging(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in admin_ids:
        staging_data["100"].clear()
        staging_data["4070"].clear()
        await update.message.reply_text("âœ… Staging list cleared.")
    else:
        await update.message.reply_text("âŒ You are not an admin.")

# Admin function to lock/unlock the well
async def lock_well(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WELL_LIMIT
    if update.message.from_user.id in admin_ids:
        WELL_LIMIT = 0
        await update.message.reply_text("ðŸ”’ Well is now **locked**. No new trucks can enter.")
    else:
        await update.message.reply_text("âŒ You are not an admin.")

async def unlock_well(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WELL_LIMIT
    if update.message.from_user.id in admin_ids:
        WELL_LIMIT = 5  # Reset to default
        await update.message.reply_text("ðŸ”“ Well is now **unlocked**. Trucks can enter again.")
    else:
        await update.message.reply_text("âŒ You are not an admin.")

# Main function to run the bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("view_status", view_status))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("staging", staging_info))
    app.add_handler(CommandHandler("addwell", add_well))
    app.add_handler(CommandHandler("removewell", remove_well))
    app.add_handler(CommandHandler("clearstaging", clear_staging))
    app.add_handler(CommandHandler("lockwell", lock_well))
    app.add_handler(CommandHandler("unlockwell", unlock_well))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
