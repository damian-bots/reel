import os
import instaloader
from pyrogram import Client, filters

# Bot Configuration
API_ID = "24620300"
API_HASH = "9a098f01aa56c836f2e34aee4b7ef963"
BOT_TOKEN = "8001341321:AAGF8SbLP-JBr5rTC6j_J6bZfRR6L8r0OQo"

bot = Client("DeadlineReelbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
loader = instaloader.Instaloader(download_video_thumbnails=False, save_metadata=False)

@bot.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("Send me an Instagram Reels link, and I'll download it for you!")

@bot.on_message(filters.text & filters.private)
def download_reel(client, message):
    url = message.text
    if "instagram.com/reel/" in url or "instagram.com/p/" in url:
        message.reply_text("Downloading... Please wait.")
        try:
            post_shortcode = url.split("/")[-2]
            
            # Load session if available to avoid checkpoint issues
            session_file = "session.json"
            if os.path.exists(session_file):
                loader.load_session_from_file("itz_tusarr", session_file)
            else:
                loader.login("itz_tusarr", "nothing1234")  # First-time login
                loader.save_session_to_file(session_file)
            
            post = instaloader.Post.from_shortcode(loader.context, post_shortcode)
            loader.download_post(post, target="downloads")
            
            # Find the downloaded video file
            for file in os.listdir("downloads"):
                if file.endswith(".mp4"):
                    video_path = os.path.join("downloads", file)
                    message.reply_video(video_path)
                    os.remove(video_path)  # Clean up after sending
                    break
        except instaloader.exceptions.BadCredentialsException:
            message.reply_text("Login failed. Please check your credentials.")
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            message.reply_text("2FA is enabled. Complete the challenge on Instagram and retry.")
        except instaloader.exceptions.CheckpointRequiredException:
            message.reply_text("Checkpoint required. Log in to Instagram and verify the challenge manually, then retry.")
        except Exception as e:
            message.reply_text(f"Error: {str(e)}")
    else:
        message.reply_text("Please send a valid Instagram Reels link!")

bot.run()
