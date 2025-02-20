import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from threading import Lock

# Replace with your bot token
BOT_TOKEN = "7290359629:AAEMevajZ9xO9YIeDn46uel0nfKNse2HMQI"

# Dictionary to track downloads per user (Use Redis or MongoDB for persistence)
user_downloads = {}
lock = Lock()

# Function to extract direct download URL from TeraBox
def get_direct_link(terabox_url):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = session.get(terabox_url, headers=headers)
    
    if "direct_link" in response.text:
        # Extract direct download link (modify this based on TeraBox's structure)
        direct_link = response.text.split('direct_link":"')[1].split('"')[0]
        return direct_link
    return None

# Function to download the video
def download_video(url, chat_id):
    filename = f"terabox_{chat_id}.mp4"
    response = requests.get(url, stream=True)

    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            file.write(chunk)

    return filename

# Handle /start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me a TeraBox video URL, and I'll download it for you! You can download up to 5 files.")

# Handle messages containing URLs
def handle_message(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    url = update.message.text.strip()

    if "terabox" not in url:
        update.message.reply_text("Please send a valid TeraBox video link.")
        return

    with lock:
        user_downloads.setdefault(chat_id, 0)
        if user_downloads[chat_id] >= 5:
            update.message.reply_text("You have reached your 5-file limit. Please try again later.")
            return
        user_downloads[chat_id] += 1

    update.message.reply_text("Fetching download link, please wait...")

    direct_url = get_direct_link(url)
    if not direct_url:
        update.message.reply_text("Failed to retrieve the direct download link. The link may be expired or protected.")
        return

    update.message.reply_text("Downloading video, please wait...")

    filename = download_video(direct_url, chat_id)
    if os.path.exists(filename):
        update.message.reply_video(video=open(filename, "rb"))
        os.remove(filename)  # Clean up
    else:
        update.message.reply_text("Failed to download the video.")

# Main function
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
