from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import random
import asyncio

app = Client("mafia_bot", api_id=24620300, api_hash="9a098f01aa56c836f2e34aee4b7ef963", bot_token="YOUR_BOT_TOKEN")

games = {}
registered_users = {}

roles = {
    "Villager": "No special abilities.",
    "Doctor": "Heals one player per night.",
    "Mafia": "Works with the Mafia to kill a player each night.",
    "Detective": "Investigates one player per night.",
    "Godfather": "Leads the Mafia and makes the final kill decision.",
    "Jester": "Wins if lynched during the day.",
    "Serial Killer": "Kills one player per night, independent of the Mafia."
}

@app.on_message(filters.command("help"))
async def start(client, message):
    await message.reply_text(
        "**🎭 Welcome to the Mafia Game! 🎭**\n\n"
        "Mafia is a strategic game of deception and deduction. Players take on secret roles and try to eliminate the opposing faction.\n\n"
        "🔹 **Night Phase:** Special roles (Mafia, Doctor, Detective, etc.) act in secrecy.\n"
        "🔹 **Day Phase:** Players discuss and vote to eliminate a suspect.\n\n"
        "💀 The game ends when either the **Mafia** or **Villagers** win!\n\n"
        "Click **/register** to join the next game!",
    )

@app.on_message(filters.command("register"))
async def register(client, message):
    chat_id = message.chat.id

    if chat_id in games:
        await message.reply_text("⚠️ A game is already in progress!")
        return

    games[chat_id] = {"players": {}, "status": "registering"}

    bot_info = await client.get_me()
    bot_username = bot_info.username

    await message.reply_text(
        "**📝 Registration Started!**\n\n"
        "Players, click the button below to register in **PM**.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Register in PM", url=f"https://t.me/{bot_username}?start=register_{chat_id}")]])
    )

    await asyncio.sleep(30)  # 30 seconds for registration
    player_count = len(games[chat_id]["players"])

    if player_count < 4:
        await app.send_message(chat_id, "⚠️ Not enough players to start the game (min 4 required). Try again later.")
        del games[chat_id]
    else:
        await start_game(client, chat_id)

@app.on_message(filters.private & filters.command("start"))
async def private_start(client, message):
    if message.text.startswith("/start register_"):
        chat_id = int(message.text.split("_")[-1])
        user_id = message.from_user.id

        if chat_id not in games or games[chat_id]["status"] != "registering":
            await message.reply_text("⚠️ No active game available to register for!")
            return

        if user_id in games[chat_id]["players"]:
            await message.reply_text("✅ You are already registered!")
            return

        registered_users[user_id] = chat_id  # Store registration context
        await message.reply_text(
            "Click below to confirm your registration.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirm Registration", callback_data="confirm_register")]])
        )

@app.on_callback_query(filters.regex("confirm_register"))
async def confirm_registration(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = registered_users.get(user_id)

    if not chat_id or chat_id not in games or games[chat_id]["status"] != "registering":
        callback_query.answer("⚠️ No active game found!", show_alert=True)
        return

    username = callback_query.from_user.username or callback_query.from_user.first_name
    games[chat_id]["players"][user_id] = {"name": username, "role": None, "alive": True}

    await callback_query.message.edit_text("✅ Registration successful! Wait for the game to start.")

    try:
        await app.send_message(chat_id, f"🔹 {username} has joined the game!")
    except:
        pass

async def start_game(client, chat_id):
    game = games[chat_id]
    game["status"] = "running"

    player_list = list(game["players"].keys())
    random.shuffle(player_list)

    assigned_roles = assign_roles(len(player_list))
    for user_id, role in zip(player_list, assigned_roles):
        game["players"][user_id]["role"] = role
        try:
            await app.send_message(user_id, f"🎭 Your role: {role}\n\n{roles[role]}")
        except:
            pass

    await app.send_message(chat_id, "🔮 The game has begun! The night phase starts now.")
    await night_phase(client, chat_id)

def assign_roles(player_count):
    role_distribution = ["Mafia", "Doctor"]
    if player_count >= 6:
        role_distribution.append("Detective")
    if player_count >= 8:
        role_distribution.append("Godfather")
    if player_count >= 9:
        role_distribution.append("Jester")
    if player_count >= 12:
        role_distribution.append("Serial Killer")

    role_distribution += ["Villager"] * (player_count - len(role_distribution))
    random.shuffle(role_distribution)
    return role_distribution

async def night_phase(client, chat_id):
    game = games[chat_id]

    for user_id, data in game["players"].items():
        if data["alive"] and data["role"] in ["Detective", "Doctor", "Mafia", "Godfather", "Serial Killer"]:
            buttons = [
                [InlineKeyboardButton(f"{game['players'][target]['name']}", callback_data=f"act_{user_id}_{target}")]
                for target in game["players"] if target != user_id and game["players"][target]["alive"]
            ]
            if buttons:
                await app.send_message(user_id, "🔪 Choose your target:", reply_markup=InlineKeyboardMarkup(buttons))

    await asyncio.sleep(30)

@app.on_callback_query(filters.regex(r"act_\d+_\d+"))
async def process_night_action(client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    actor_id, target_id = int(parts[1]), int(parts[2])
    
    for chat_id, game in games.items():
        if actor_id in game["players"]:
            role = game["players"][actor_id]["role"]
            target_name = game["players"][target_id]["name"]

            if role == "Mafia":
                await app.send_message(chat_id, f"☠️ The Mafia has chosen to attack {target_name}.")
            elif role == "Doctor":
                await app.send_message(chat_id, f"🚑 The Doctor has chosen to heal {target_name}.")
            elif role == "Detective":
                await app.send_message(chat_id, f"🔍 The Detective investigated {target_name} and found their role: {game['players'][target_id]['role']}.")
            elif role == "Serial Killer":
                await app.send_message(chat_id, f"🔪 The Serial Killer has attacked {target_name}.")

            break

    await callback_query.message.edit_text("✅ Action recorded! Waiting for other players.")

app.run()
