from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# In-memory staging system
staging_areas = {
    "4070": [],
    "100": [],
    "well": []
}

MAX_WELL_CAPACITY = 5 # Limit for trucks at the well

# Function to handle staging
async def handle_staging(update: Update, context: CallbackContext):
    text = update.message.text.strip().lower()
    driver_id = update.message.from_user.id
    driver_name = update.message.from_user.full_name

    if text not in ["4070", "100"]:
        return # Ignore other messages

    # Check if the driver is already staged
    for area in staging_areas:
        if driver_id in [truck["id"] for truck in staging_areas[area]]:
            await update.message.reply_text(f"{driver_name}, you are already staged in {area}.")
            return

    # Prioritize 100 trucks at the well (keep 5 at all times)
    if text == "100":
        if len(staging_areas["well"]) < MAX_WELL_CAPACITY:
            staging_areas["well"].append({"id": driver_id, "name": driver_name})
            await update.message.reply_text(f"{driver_name}, you are assigned to THE WELL (Priority: 100). ✅")
        else:
            staging_areas["100"].append({"id": driver_id, "name": driver_name})
            await update.message.reply_text(f"{driver_name}, the well is full. You have been staged in the 100 group. 🚛")
    else:
        # 4070 trucks are staged until manually called
        staging_areas["4070"].append({"id": driver_id, "name": driver_name})
        await update.message.reply_text(f"{driver_name}, you are staged in the 4070 group. Wait until called to the well.")

# Command to manually call trucks to the well
async def callwell(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /callwell [number]")
        return

    try:
        num_trucks = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid number! Use: /callwell [number]")
        return

    if len(staging_areas["well"]) >= MAX_WELL_CAPACITY:
        await update.message.reply_text("The well is already full. Wait for space to open up.")
        return

    moved_trucks = 0
    while moved_trucks < num_trucks and len(staging_areas["well"]) < MAX_WELL_CAPACITY:
        # Prioritize 100 trucks first
        if staging_areas["100"]:
            next_truck = staging_areas["100"].pop(0)
        elif staging_areas["4070"]:
            next_truck = staging_areas["4070"].pop(0)
        else:
            break

        staging_areas["well"].append(next_truck)
        moved_trucks += 1
        await update.message.reply_text(f"{next_truck['name']} has been moved to THE WELL. ✅")

    if moved_trucks == 0:
        await update.message.reply_text("No trucks available to call to the well.")

# Command to check current staging status
async def staging_status(update: Update, context: CallbackContext):
    message = "**📋 Current Staging Status:**\n\n"
    
    for area, trucks in staging_areas.items():
        message += f"**{area.upper()} ({len(trucks)} trucks)**\n"
        if trucks:
            for truck in trucks:
                message += f" - {truck['name']}\n"
        else:
            message += " - No trucks staged.\n"
        message += "\n"

    await update.message.reply_text(message, parse_mode="Markdown")

# Command to remove a truck when it leaves
async def leave(update: Update, context: CallbackContext):
    driver_id = update.message.from_user.id
    driver_name = update.message.from_user.full_name

    removed = False
    for area in staging_areas:
        if driver_id in [truck["id"] for truck in staging_areas[area]]:
            staging_areas[area] = [truck for truck in staging_areas[area] if truck["id"] != driver_id]
            removed = True
            break

    if removed:
        await update.message.reply_text(f"{driver_name}, you have been removed from staging. ✅")
    else:
        await update.message.reply_text(f"{driver_name}, you were not staged anywhere.")

# Alternative commands for leaving
async def leave_alias(update: Update, context: CallbackContext):
    await leave(update, context)

# Main function to run the bot
def main():
    application = Application.builder().token("YOUR_API_TOKEN").build()

    application.add_handler(CommandHandler("status", staging_status))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(CommandHandler("lv", leave_alias))
    application.add_handler(CommandHandler("lve", leave_alias))
    application.add_handler(CommandHandler("callwell", callwell))
    
    # Handle text messages (4070 or 100)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_staging))

    application.run_polling()

if __name__ == '__main__':
    main()


On Mon, Feb 3, 2025, 9:50 PM Meace Mcmillian <meace47@gmail.com> wrote:
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# In-memory staging system
staging_areas = {
    "4070": [],
    "100": [],
    "well": []
}

MAX_WELL_CAPACITY = 5 # Limit for trucks at the well

# Command to stage a truck
async def stage(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /stage [4070 | 100]")
        return

    truck_type = context.args[0].lower()

    if truck_type not in ["4070", "100"]:
        await update.message.reply_text("Invalid type! Use 4070 or 100.")
        return

    driver_id = update.message.from_user.id
    driver_name = update.message.from_user.full_name

    # Check if the driver is already staged
    for area in staging_areas:
        if driver_id in [truck["id"] for truck in staging_areas[area]]:
            await update.message.reply_text(f"{driver_name}, you are already staged in {area}.")
            return

    # Prioritize 100 trucks at the well (keep 5 at all times)
    if truck_type == "100":
        if len(staging_areas["well"]) < MAX_WELL_CAPACITY:
            staging_areas["well"].append({"id": driver_id, "name": driver_name})
            await update.message.reply_text(f"{driver_name}, you are assigned to THE WELL (Priority: 100). ✅")
        else:
            staging_areas["100"].append({"id": driver_id, "name": driver_name})
            await update.message.reply_text(f"{driver_name}, the well is full. You have been staged in the 100 group. 🚛")
    else:
        # 4070 trucks are staged until manually called
        staging_areas["4070"].append({"id": driver_id, "name": driver_name})
        await update.message.reply_text(f"{driver_name}, you are staged in the 4070 group. Wait until called to the well.")

# Command to manually call trucks to the well
async def callwell(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /callwell [number]")
        return

    try:
        num_trucks = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid number! Use: /callwell [number]")
        return

    if len(staging_areas["well"]) >= MAX_WELL_CAPACITY:
        await update.message.reply_text("The well is already full. Wait for space to open up.")
        return

    moved_trucks = 0
    while moved_trucks < num_trucks and len(staging_areas["well"]) < MAX_WELL_CAPACITY:
        # Prioritize 100 trucks first
        if staging_areas["100"]:
            next_truck = staging_areas["100"].pop(0)
        elif staging_areas["4070"]:
            next_truck = staging_areas["4070"].pop(0)
        else:
            break

        staging_areas["well"].append(next_truck)
        moved_trucks += 1
        await update.message.reply_text(f"{next_truck['name']} has been moved to THE WELL. ✅")

    if moved_trucks == 0:
        await update.message.reply_text("No trucks available to call to the well.")

# Command to check current staging status
async def staging_status(update: Update, context: CallbackContext):
    message = "**📋 Current Staging Status:**\n\n"
    
    for area, trucks in staging_areas.items():
        message += f"**{area.upper()} ({len(trucks)} trucks)**\n"
        if trucks:
            for truck in trucks:
                message += f" - {truck['name']}\n"
        else:
            message += " - No trucks staged.\n"
        message += "\n"

    await update.message.reply_text(message, parse_mode="Markdown")

# Command to remove a truck when it leaves
async def leave(update: Update, context: CallbackContext):
    driver_id = update.message.from_user.id
    driver_name = update.message.from_user.full_name

    removed = False
    for area in staging_areas:
        if driver_id in [truck["id"] for truck in staging_areas[area]]:
            staging_areas[area] = [truck for truck in staging_areas[area] if truck["id"] != driver_id]
            removed = True
            break

    if removed:
        await update.message.reply_text(f"{driver_name}, you have been removed from staging. ✅")
    else:
        await update.message.reply_text(f"{driver_name}, you were not staged anywhere.")

# Alternative commands for leaving
async def leave_alias(update: Update, context: CallbackContext):
    await leave(update, context)

# Main function to run the bot
def main():
    application = Application.builder().token("8029048707:AAGfxjlxZAIPkPS93a9BZ9w-Ku8-ywT5I-M").build()

    application.add_handler(CommandHandler("stage", stage))
    application.add_handler(CommandHandler("status", staging_status))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(CommandHandler("lv", leave_alias))
    application.add_handler(CommandHandler("lve", leave_alias))
    application.add_handler(CommandHandler("callwell", callwell))

    application.run_polling()

if __name__ == '__main__':
    main()
