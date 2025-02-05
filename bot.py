import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = "8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M"

# Truck staging and well management
staging_data = {"4070": [], "100": [], "well": []}
WELL_LIMIT = 5
admin_ids = [123456789]  # Replace with actual admin Telegram IDs

# Function to display truck options
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ðŸš› 4070", callback_data="4070")],
        [InlineKeyboardButton("ðŸ›» 100", callback_data="100")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose your truck type:", reply_markup=reply_markup)

# Function to handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    truck_type = query.data

    if truck_type in ["4070", "100"]:
        keyboard = [
            [InlineKeyboardButton("ðŸ›‘ Chassis Out", callback_data=f"chassis_out_{truck_type}")],
            [InlineKeyboardButton("â¬…ï¸ Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"You selected {truck_type}. Do you want to Chassis Out?", reply_markup=reply_markup)

    elif "chassis_out" in truck_type:
        _, selected_type = truck_type.split("_")
        await process_chassis_out(query, selected_type, user_id, context)

    elif query.data == "leave_well":
        await process_leave_well(query, user_id, context)

    elif query.data == "back":
        await start(update, context)

# Function to process chassis out
async def process_chassis_out(query, truck_type, user_id, context):
    if len(staging_data["well"]) < WELL_LIMIT:
        staging_data["well"].append(user_id)
        await query.edit_message_text(f"âœ… You have been sent to the well as {truck_type} (CO).")
    else:
        staging_data[truck_type].append(user_id)
        await query.edit_message_text(f"ðŸš§ Well is full. You are staged as {truck_type}.")

# Function to process leaving well
async def process_leave_well(query, user_id, context):
    if user_id in staging_data["well"]:
        staging_data["well"].remove(user_id)
        await query.edit_message_text("âœ… You have left the well.")
        await move_next_to_well(context)
    else:
        await query.edit_message_text("âš ï¸ You are not at the well.")

# Function to move the next truck to the well
async def move_next_to_well(context):
    if len(staging_data["well"]) < WELL_LIMIT:
        if staging_data["100"]:
            next_truck = staging_data["100"].pop(0)
            staging_data["well"].append(next_truck)
        elif staging_data["4070"]:
            next_truck = staging_data["4070"].pop(0)
            staging_data["well"].append(next_truck)

# Admin function to manually add a truck to the well
async def add_well(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in admin_ids:
        truck_num = int(context.args[0]) if context.args else None
        truck_list = staging_data["100"] + staging_data["4070"]
        
        if 0 < truck_num <= len(truck_list):
            selected_truck = truck_list[truck_num - 1]
            if len(staging_data["well"]) < WELL_LIMIT:
                staging_data["well"].append(selected_truck)
                await update.message.reply_text(f"âœ… Truck #{truck_num} added to the well.")
            else:
                await update.message.reply_text("ðŸš§ Well is full!")
        else:
            await update.message.reply_text("âš ï¸ Invalid truck number.")
    else:
        await update.message.reply_text("âŒ You are not an admin.")

# Function to display staging info with numbers
async def staging_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📋 **Staging Information:**\n\n"

    msg += "**WELL:**\n"
    for i, truck in enumerate(staging_data["well"], 1):
        msg += f"🔵 #{i}: Truck {truck}\n"

    msg += "\n**100 Mesh Staging:**\n"
    for i, truck in enumerate(staging_data["100"], 1):
        msg += f"🟢 #{i}: Truck {truck}\n"

    msg += "\n**4070 Staging:**\n"
    for i, truck in enumerate(staging_data["4070"], 1):
        msg += f"🟠 #{i}: Truck {truck}\n"

    await update.message.reply_text(msg)
        msg += f"ðŸ”µ #{i}: Truck {truck}
"

    msg += "**100 Mesh Staging:**
"
    for i, truck in enumerate(staging_data["100"], 1):
        msg += f"ðŸŸ¢ #{i}: Truck {truck}
"

    msg += "**4070 Staging:**
"
    for i, truck in enumerate(staging_data["4070"], 1):
        msg += f"ðŸŸ  #{i}: Truck {truck}
"

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
