import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "YOUR_BOT_TOKEN"

# Dictionary to store truck staging info
staging_data = {"4070": [], "100": [], "well": []}

# Function to show main menu buttons
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
    await query.answer()  # Acknowledge the button press
    truck_type = query.data

    if truck_type in ["4070", "100"]:
        keyboard = [
            [InlineKeyboardButton("ðŸ›‘ Chassis Out", callback_data="chassis_out")],
            [InlineKeyboardButton("â¬…ï¸ Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"You selected {truck_type}. Do you want to Chassis Out?", reply_markup=reply_markup)

    elif truck_type == "chassis_out":
        await query.edit_message_text("âœ… You have successfully **Chassis Out**. Thank you!")

    elif truck_type == "back":
        await start(update, context)

# Function to stage a truck
async def stage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    truck_type = context.args[0] if context.args else None
    user_id = update.message.from_user.id

    if truck_type in ["4070", "100"]:
        if user_id not in staging_data[truck_type]:
            staging_data[truck_type].append(user_id)
            await update.message.reply_text(f"âœ… You have been staged as {truck_type}.")
        else:
            await update.message.reply_text("âš ï¸ You are already staged.")
    else:
        await update.message.reply_text("âŒ Invalid truck type. Use `/stage 4070` or `/stage 100`.")

# Function to remove a truck from staging
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    removed = False

    for key in staging_data.keys():
        if user_id in staging_data[key]:
            staging_data[key].remove(user_id)
            removed = True
            await update.message.reply_text(f"âœ… You have left the {key} staging area.")

    if not removed:
        await update.message.reply_text("âš ï¸ You are not staged.")

# Function to call trucks to the well
async def callwell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num_trucks = int(context.args[0]) if context.args else 1

    if len(staging_data["100"]) >= num_trucks:
        called_trucks = staging_data["100"][:num_trucks]
        staging_data["well"].extend(called_trucks)
        del staging_data["100"][:num_trucks]

        await update.message.reply_text(f"âœ… {num_trucks} trucks have been called to the well!")
    else:
        await update.message.reply_text("âš ï¸ Not enough trucks staged to move to the well.")

# Function to display staging info
async def staging_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📋 **Staging Information:**\n"
    
    for key, trucks in staging_data.items():
        msg += f"➡️ **{key.upper()}**: {len(trucks)} trucks staged\n"

    await update.message.reply_text(msg)

# Main function to run the bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("stage", stage))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("callwell", callwell))
    app.add_handler(CommandHandler("staging", staging_info))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
