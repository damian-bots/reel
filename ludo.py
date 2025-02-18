from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import random
import asyncio

# Initialize bot
app = Client("ludo_bot", api_id=24620300, api_hash="9a098f01aa56c836f2e34aee4b7ef963", bot_token="7290359629:AAEMevajZ9xO9YIeDn46uel0nfKNse2HMQI")

games = {}  # Stores ongoing games

# Start command
@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text(
        "Welcome to Ludo Inline Game! Click below to start a new game:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Start Game", callback_data="start_ludo")]
        ])
    )

# Start a new game
@app.on_callback_query(filters.regex("start_ludo"))
def new_game(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name

    if chat_id in games:
        callback_query.answer("A game is already in progress!", show_alert=True)
        return

    games[chat_id] = {
        "players": {user_id: {"name": username, "position": 0}},
        "turn_order": [user_id],
        "current_turn": 0,
        "game_active": True
    }

    callback_query.message.edit(
        f"Ludo game started! Players: @{username}\n\nWaiting for more players...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Game", callback_data="join_ludo")],
            [InlineKeyboardButton("Start Match", callback_data="start_match")]
        ])
    )

# Join an existing game
@app.on_callback_query(filters.regex("join_ludo"))
def join_game(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name

    if chat_id not in games or not games[chat_id]["game_active"]:
        callback_query.answer("No active game to join!", show_alert=True)
        return

    if user_id in games[chat_id]["players"]:
        callback_query.answer("You have already joined!", show_alert=True)
        return

    if len(games[chat_id]["players"]) >= 4:
        callback_query.answer("Game is full (max 4 players)!", show_alert=True)
        return

    games[chat_id]["players"][user_id] = {"name": username, "position": 0}
    games[chat_id]["turn_order"].append(user_id)

    players_list = "\n".join([f"@{p['name']}" for p in games[chat_id]["players"].values()])
    callback_query.message.edit(
        f"Ludo game started! Players:\n{players_list}\n\nWaiting for more players...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Game", callback_data="join_ludo")],
            [InlineKeyboardButton("Start Match", callback_data="start_match")]
        ])
    )

# Start the match
@app.on_callback_query(filters.regex("start_match"))
def start_match(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    if chat_id not in games or not games[chat_id]["game_active"]:
        callback_query.answer("No active game to start!", show_alert=True)
        return

    if len(games[chat_id]["players"]) < 2:
        callback_query.answer("At least 2 players are required!", show_alert=True)
        return

    current_player_id = games[chat_id]["turn_order"][0]
    current_player_name = games[chat_id]["players"][current_player_id]["name"]
    
    callback_query.message.edit(
        f"Match started! 🎲 {current_player_name}, it's your turn to roll!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Roll Dice 🎲", callback_data="roll_dice")]
        ])
    )

# Roll dice
@app.on_callback_query(filters.regex("roll_dice"))
def roll_dice(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    
    if chat_id not in games or not games[chat_id]["game_active"]:
        callback_query.answer("No active game!", show_alert=True)
        return

    game = games[chat_id]
    current_player_id = game["turn_order"][game["current_turn"]]
    
    if user_id != current_player_id:
        callback_query.answer("Wait for your turn!", show_alert=True)
        return

    dice_value = random.randint(1, 6)
    game["players"][user_id]["position"] += dice_value
    position = game["players"][user_id]["position"]
    
    if position >= 30:  # Winning condition (reaching 30 points)
        callback_query.message.edit(f"🎉 @{game['players'][user_id]['name']} has won the game! 🎉")
        del games[chat_id]
        return
    
    next_turn = (game["current_turn"] + 1) % len(game["turn_order"])
    game["current_turn"] = next_turn
    next_player_id = game["turn_order"][next_turn]
    next_player_name = game["players"][next_player_id]["name"]
    
    callback_query.message.edit(
        f"🎲 @{game['players'][user_id]['name']} rolled a {dice_value} (Position: {position})\n\n"
        f"Next turn: {next_player_name}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Roll Dice 🎲", callback_data="roll_dice")]
        ])
    )

app.run()
