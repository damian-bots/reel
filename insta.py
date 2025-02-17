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

# Load or login to Instagram session
SESSION_FILE = "session.json"
USERNAME = "itz_tusarr"
PASSWORD = "nothing1234"

if os.path.exists(SESSION_FILE):
    loader.load_session_from_file(USERNAME, SESSION_FILE)
else:
    try:
        loader.login(USERNAME, PASSWORD)
        loader.save_session_to_file(SESSION_FILE)
    except instaloader.exceptions.BadCredentialsException:
        print("Invalid Instagram credentials.")
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        print("2FA required. Complete authentication manually.")

# Flask App Setup
app = Flask(__name__)

@app.route('/download', methods=['GET'])
def download_reel():
    url = request.args.get('url')
    if not url or ("instagram.com/reel/" not in url and "instagram.com/p/" not in url):
        return jsonify({"error": "Invalid Instagram Reels URL."}), 400
    
    try:
        post_shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, post_shortcode)
        
        if post.is_video:
            return jsonify({"content_url": post.video_url, "content_type": "video"})
        else:
            return jsonify({"content_url": post.url, "content_type": "photo"})
    
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        return jsonify({"error": "This profile is private. Cannot download content."}), 403
    except instaloader.exceptions.QueryReturnedNotFoundException:
        return jsonify({"error": "Content not found. Please check the URL."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bot.on_message(filters.command("start"))
async def start_command(_, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Channel 📢", url="https://t.me/DeadlineTech")],
        [InlineKeyboardButton("Support 💬", url="https://t.me/DeadlineTechsupport")]
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
        post_shortcode = link.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, post_shortcode)
        
        if post.is_video:
            await message.reply_video(post.video_url)
        else:
            await message.reply_photo(post.url)
    
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        await message.reply("This profile is private. Cannot download content.")
    except instaloader.exceptions.QueryReturnedNotFoundException:
        await message.reply("Content not found. Please check the URL.")
    except Exception as e:
        print(e)
        await message.reply("An error occurred while processing the request.")

if __name__ == '__main__':
    bot.run()
    app.run(host='4.213.247.72', port=22)
