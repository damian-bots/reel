from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
import random
import asyncio
import time

app = Client("mafia_bot", api_id=24620300, api_hash="9a098f01aa56c836f2e34aee4b7ef963", bot_token="7290359629:AAEMevajZ9xO9YIeDn46uel0nfKNse2HMQI")

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

NIGHT_GIF = "https://media.giphy.com/media/LmNwrBhejkK9EFP504/giphy.gif"
DAY_GIF = "https://media.giphy.com/media/WF9evUeT4cudYZtPVF/giphy.gif"

@app.on_message(filters.command("help"))
async def start(client, message):
    await message.reply_text(
        "**🎭 Welcome to the Mafia Game! 🎭**\n\n"
        "Click **/register** to join the next game!"
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
        "Players, click below to register in **PM**.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Register", url=f"https://t.me/{bot_username}?start=register_{chat_id}")]])
    )

    await asyncio.sleep(30)

    if len(games[chat_id]["players"]) < 4:
        await app.send_message(chat_id, "⚠️ Not enough players (min 4). Try again later.")
        del games[chat_id]
    else:
        await start_game(client, chat_id)

@app.on_message(filters.private & filters.command("start"))
async def private_start(client, message):
    if message.text.startswith("/start register_"):
        chat_id = int(message.text.split("_")[-1])
        user_id = message.from_user.id

        if chat_id not in games or games[chat_id]["status"] != "registering":
            await message.reply_text("⚠️ No active game available!")
            return

        if user_id in games[chat_id]["players"]:
            await message.reply_text("✅ You are already registered!")
            return

        registered_users[user_id] = chat_id
        await message.reply_text(
            "Click below to confirm registration.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirm", callback_data="confirm_register")]])
        )

@app.on_callback_query(filters.regex("confirm_register"))
async def confirm_registration(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = registered_users.get(user_id)

    if not chat_id or chat_id not in games or games[chat_id]["status"] != "registering":
        await callback_query.answer("⚠️ No active game found!", show_alert=True)
        return

    username = callback_query.from_user.username or callback_query.from_user.first_name
    games[chat_id]["players"][user_id] = {"name": username, "role": None, "alive": True, "lynched": False}

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
    await app.send_animation(chat_id, NIGHT_GIF, caption="🌙 Night falls. Everyone goes to sleep...")
    await asyncio.sleep(5)

    await day_phase(client, chat_id)

async def day_phase(client, chat_id):
    await app.send_animation(chat_id, DAY_GIF, caption="☀️ The sun rises. A new day begins!")
    await asyncio.sleep(5)

    buttons = [[InlineKeyboardButton(game["players"][uid]["name"], callback_data=f"lynch_{uid}")]
               for uid, data in games[chat_id]["players"].items() if data["alive"]]

    await app.send_message(
        chat_id, "🗳 Vote to lynch a player (30s):",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await asyncio.sleep(30)

    target_id = random.choice([uid for uid, data in games[chat_id]["players"].items() if data["alive"]])
    games[chat_id]["players"][target_id]["alive"] = False

    await mute_player(chat_id, target_id)
    await app.send_message(chat_id, f"⚖️ {games[chat_id]['players'][target_id]['name']} was lynched!")

    await check_win_condition(client, chat_id)

async def mute_player(chat_id, user_id):
    try:
        await app.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
    except:
        pass

async def check_win_condition(client, chat_id):
    game = games[chat_id]
    mafia_alive = any(data["role"] in ["Mafia", "Godfather"] and data["alive"] for data in game["players"].values())
    villagers_alive = any(data["role"] == "Villager" and data["alive"] for data in game["players"].values())

    if not mafia_alive:
        await app.send_message(chat_id, "🎉 Villagers win!")
    elif not villagers_alive:
        await app.send_message(chat_id, "💀 Mafia wins!")
    else:
        await night_phase(client, chat_id)

app.run()
