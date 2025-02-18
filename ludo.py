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
        username = message.from_user.username or message.from_user.first_name

        if chat_id not in games or games[chat_id]["status"] != "registering":
            await message.reply_text("⚠️ No active game available to register for!")
            return

        if user_id in games[chat_id]["players"]:
            await message.reply_text("✅ You are already registered!")
            return

        registered_users[user_id] = chat_id  # Store where they are registering from
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
    
    callback_query.message.edit_text("✅ Registration successful! Wait for the game to start.")
    
    try:
        await app.send_message(chat_id, f"🔹 {username} has joined the game!")
    except:
        pass  # Ignore if the group can't be messaged

async def start_game(client, chat_id):
    game = games[chat_id]
    game["status"] = "running"

    player_list = list(game["players"].keys())
    random.shuffle(player_list)

    # Assign roles dynamically
    assigned_roles = assign_roles(len(player_list))
    for user_id, role in zip(player_list, assigned_roles):
        game["players"][user_id]["role"] = role
        try:
            await app.send_message(user_id, f"🎭 Your role: {role}\n\n{roles[role]}")
        except:
            pass  # Ignore if user can't be messaged

    await app.send_message(
        chat_id,
        "🔮 The game has begun! The night phase starts now.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Update Status", callback_data="update_status")]])
    )
    await night_phase(client, chat_id)

def assign_roles(player_count):
    role_distribution = ["Mafia", "Doctor"]  # Minimum roles for 4 players
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
            buttons = [[InlineKeyboardButton(f"{info['name']}", callback_data=f"night_{data['role']}_{target}")]
                       for target, info in game["players"].items() if target != user_id and info["alive"]]
            await app.send_message(user_id, "🔪 Choose your target:", reply_markup=InlineKeyboardMarkup(buttons))

    await asyncio.sleep(30)
    await check_win_condition(client, chat_id)

async def check_win_condition(client, chat_id):
    game = games.get(chat_id, None)
    if not game:
        return

    mafia_alive = any(data["role"] in ["Mafia", "Godfather"] and data["alive"] for data in game["players"].values())
    villagers_alive = any(data["role"] == "Villager" and data["alive"] for data in game["players"].values())
    serial_killer_alive = any(data["role"] == "Serial Killer" and data["alive"] for data in game["players"].values())
    jester_won = any(data.get("lynched") and data["role"] == "Jester" for data in game["players"].values())

    if jester_won:
        await app.send_message(chat_id, "🎭 The Jester was lynched and wins the game!")
        del games[chat_id]
        return

    if serial_killer_alive and not mafia_alive and not villagers_alive:
        await app.send_message(chat_id, "🔪 The Serial Killer has eliminated everyone and wins the game!")
        del games[chat_id]
        return

    if not mafia_alive:
        await app.send_message(chat_id, "🎉 The Villagers have defeated the Mafia! Villagers win!")
        del games[chat_id]
        return

    if not villagers_alive:
        await app.send_message(chat_id, "😈 The Mafia have taken over! Mafia wins!")
        del games[chat_id]
        return
        
app.run()
