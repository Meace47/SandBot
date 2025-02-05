import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = "8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M"

# Truck staging and well management
staging_data = {"4070": [], "100": [], "well": []}
WELL_LIMIT = 5

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
        staging_data["well"].append((user_id, f"{truck_type} (CO)"))
        await query.edit_message_text(f"âœ… You have been sent to the well as {truck_type} (CO).")
    else:
        staging_data[truck_type].append(user_id)
        await query.edit_message_text(f"ðŸš§ Well is full. You are staged as {truck_type}.")

# Function to process leaving well
async def process_leave_well(query, user_id, context):
    if user_id in [t[0] for t in staging_data["well"]]:
        staging_data["well"] = [t for t in staging_data["well"] if t[0] != user_id]
        await query.edit_message_text("âœ… You have left the well.")

        # Automatically move the next truck to the well
        await move_next_to_well(context)
    else:
        await query.edit_message_text("âš ï¸ You are not at the well.")

# Function to move the next truck to the well
async def move_next_to_well(context):
    if len(staging_data["well"]) < WELL_LIMIT:
        if staging_data["100"]:
            next_truck = staging_data["100"].pop(0)
            staging_data["well"].append((next_truck, "100"))
        elif staging_data["4070"]:
            next_truck = staging_data["4070"].pop(0)
            staging_data["well"].append((next_truck, "4070"))

# Function to display staging info
async def staging_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "ðŸ“‹ **Staging Information:**
"
    for key, trucks in staging_data.items():
        msg += f"âž¡ï¸ **{key.upper()}**: {len(trucks)} trucks staged
"
    await update.message.reply_text(msg)

# Main function to run the bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("staging", staging_info))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
