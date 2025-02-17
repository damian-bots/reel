import os
import requests
import instaloader
from flask import Flask, request, jsonify
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Bot Configuration
API_ID = "24620300"
API_HASH = "9a098f01aa56c836f2e34aee4b7ef963"
BOT_TOKEN = "8001341321:AAGF8SbLP-JBr5rTC6j_J6bZfRR6L8r0OQo"

bot = Client("insta_reels_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
loader = instaloader.Instaloader(download_video_thumbnails=False, save_metadata=False)

# Flask App Setup
app = Flask(__name__)
API_URL = "https://karma-api2.vercel.app/instadl"
DOWNLOADING_STICKER_ID = (
    "CAACAgIAAx0CXfD_PwAC3X5lerw5fHE4kK-etOOqml5aYiHUNgAC2yYAAtBFgUq6SfkuZdHvGR4E"
)

@app.route('/download', methods=['GET'])
def download_reel():
    url = request.args.get('url')
    if not url or ("instagram.com/reel/" not in url and "instagram.com/p/" not in url):
        return jsonify({"error": "Invalid Instagram Reels URL."}), 400
    
    try:
        response = requests.get(API_URL, params={"url": url})
        data = response.json()

        if "content_url" in data:
            content_url = data["content_url"]
            content_type = "video" if "video" in content_url else "photo"
            return jsonify({"content_url": content_url, "content_type": content_type})
        else:
            return jsonify({"error": "Unable to fetch content. Please check the Instagram URL."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bot.on_message(filters.command("start"))
async def start_command(_, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Channel", url="https://t.me/yourchannel")],
        [InlineKeyboardButton("Support", url="https://t.me/yoursupport")]
    ])
    await message.reply_text(
        "**Welcome to Instagram Reels Downloader Bot!**\n\nSend me an Instagram Reel link, and I'll download it for you.",
        reply_markup=buttons
    )

@bot.on_message(filters.text & filters.private)
async def direct_download_handler(_, message: Message):
    link = message.text.strip()
    if "instagram.com/reel/" not in link and "instagram.com/p/" not in link:
        await message.reply("Please send a valid Instagram Reels link!")
        return
    
    try:
        downloading_sticker = await message.reply_sticker(DOWNLOADING_STICKER_ID)
        response = requests.get(API_URL, params={"url": link})
        data = response.json()

        if "content_url" in data:
            content_url = data["content_url"]
            content_type = "video" if "video" in content_url else "photo"

            if content_type == "photo":
                await message.reply_photo(content_url)
            elif content_type == "video":
                await message.reply_video(content_url)
            else:
                await message.reply("Unsupported content type.")
        else:
            await message.reply("Unable to fetch content. Please check the Instagram URL.")
    except Exception as e:
        print(e)
        await message.reply("An error occurred while processing the request.")
    finally:
        await downloading_sticker.delete()

if __name__ == '__main__':
    bot.run()
    app.run(host='0.0.0.0', port=5000)
