from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import random

# Store game data
games = {}

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    games[chat_id] = {
        "players": {},
        "turn_order": [],
        "current_turn": 0,
    }
    keyboard = [[InlineKeyboardButton("Join Game", callback_data="join")]]
    update.message.reply_text("Ludo Game Started! Click to join.", 
                              reply_markup=InlineKeyboardMarkup(keyboard))

def join_game(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    username = query.from_user.first_name
    
    if chat_id not in games or len(games[chat_id]["players"]) >= 4:
        query.answer("Game is full or not started!")
        return
    
    if user_id not in games[chat_id]["players"]:
        games[chat_id]["players"][user_id] = {"position": 0}
        games[chat_id]["turn_order"].append(user_id)
        query.answer(f"{username} joined!")
        query.message.edit_text(f"Players: {', '.join([context.bot.get_chat_member(chat_id, pid).user.first_name for pid in games[chat_id]['players']])}\nWaiting for more players or /roll to start!")
    else:
        query.answer("You are already in the game!")

def roll_dice(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in games or len(games[chat_id]["players"]) < 2:
        update.message.reply_text("At least 2 players needed to start!")
        return
    
    turn = games[chat_id]["current_turn"]
    player_id = games[chat_id]["turn_order"][turn]
    dice_roll = random.randint(1, 6)
    games[chat_id]["players"][player_id]["position"] += dice_roll
    player_name = context.bot.get_chat_member(chat_id, player_id).user.first_name
    
    message = f"{player_name} rolled a {dice_roll}! New position: {games[chat_id]['players'][player_id]['position']}"
    
    games[chat_id]["current_turn"] = (turn + 1) % len(games[chat_id]["turn_order"])
    update.message.reply_text(message)

def main():
    updater = Updater("7290359629:AAEMevajZ9xO9YIeDn46uel0nfKNse2HMQI", use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(join_game, pattern="^join$"))
    dp.add_handler(CommandHandler("roll", roll_dice))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
