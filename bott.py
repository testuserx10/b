import discord
from discord.ext import commands
import json
import os

# ------------------ SECRETS ------------------
TOKEN = os.getenv("TOKEN")  # Discord bot token
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Channel ID as integer
# --------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load existing JSON or create empty
JSON_FILE = "data.json"
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
else:
    data = {}

LIST_MESSAGE_ID = None  # Will store the ID of the list message

def save_json():
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def update_list_message(channel):
    """Update the list message content, numbered."""
    global LIST_MESSAGE_ID
    if not data:
        content = "No items."
    else:
        content = "**Current List:**\n" + "\n".join(f"{i+1}. {k}" for i, k in enumerate(data.keys()))
    
    list_message = None
    if LIST_MESSAGE_ID:
        try:
            list_message = await channel.fetch_message(LIST_MESSAGE_ID)
        except:
            LIST_MESSAGE_ID = None
    
    if list_message:
        await list_message.edit(content=content)
    else:
        # Get the first (oldest) message in the channel
        async for msg in channel.history(limit=1, oldest_first=True):
            list_message = msg
        if list_message:
            LIST_MESSAGE_ID = list_message.id
            await list_message.edit(content=content)
        else:
            # Channel is empty, send a new message
            list_message = await channel.send(content)
            LIST_MESSAGE_ID = list_message.id

@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await update_list_message(channel)

@bot.event
async def on_message(message):
    global LIST_MESSAGE_ID

    if message.author == bot.user:
        return

    if message.channel.id != CHANNEL_ID:
        return

    content = message.content.strip()
    lower = content.lower()

    # ADD (case-insensitive, comma separated)
    if lower.startswith("add "):
        items = content[4:].split(",")
        for item in items:
            key = item.strip()
            if key:
                data[key] = key
        save_json()
        await update_list_message(message.channel)

    # DEL (case-insensitive, comma separated, numbers OR names)
    elif lower.startswith("del "):
        args = content[4:].split(",")
        keys_list = list(data.keys())

        for arg in args:
            arg = arg.strip()
            if not arg:
                continue

            # Delete by number
            if arg.isdigit():
                index = int(arg) - 1
                if 0 <= index < len(keys_list):
                    data.pop(keys_list[index], None)

            # Delete by name
            else:
                data.pop(arg, None)

        save_json()
        await update_list_message(message.channel)

    # CLEAR
    elif lower == "clear":
        data.clear()
        save_json()
        await update_list_message(message.channel)

    # Delete every message in this channel
    try:
        await message.delete()
    except:
        pass

# Run the bot
if not TOKEN or not CHANNEL_ID:
    raise RuntimeError("TOKEN or CHANNEL_ID not set in environment variables")

bot.run(TOKEN)
