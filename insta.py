import os
import instaloader
from flask import Flask, request, send_file, jsonify
from pyrogram import Client, filters

# Bot Configuration
API_ID = "24620300"
API_HASH = "9a098f01aa56c836f2e34aee4b7ef963"
BOT_TOKEN = "8001341321:AAGF8SbLP-JBr5rTC6j_J6bZfRR6L8r0OQo"

bot = Client("insta_reels_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
loader = instaloader.Instaloader(download_video_thumbnails=False, save_metadata=False)

# Flask App Setup
app = Flask(__name__)

@app.route('/download', methods=['GET'])
def download_reel():
    url = request.args.get('url')
    if not url or ("instagram.com/reel/" not in url and "instagram.com/p/" not in url):
        return jsonify({"error": "Invalid Instagram Reels URL."}), 400
    
    try:
        post_shortcode = url.split("/")[-2]
        session_file = "session.json"

        if os.path.exists(session_file):
            loader.load_session_from_file("itz_tusarr", session_file)
        else:
            loader.login("itz_tusarr", "nothing1234")  # First-time login
            loader.save_session_to_file(session_file)
        
        post = instaloader.Post.from_shortcode(loader.context, post_shortcode)
        loader.download_post(post, target="downloads")
        
        for file in os.listdir("downloads"):
            if file.endswith(".mp4"):
                video_path = os.path.join("downloads", file)
                return send_file(video_path, as_attachment=True)
        
        return jsonify({"error": "Video not found after download."}), 500
    except instaloader.exceptions.BadCredentialsException:
        return jsonify({"error": "Login failed. Check your credentials."}), 401
    except instaloader.exceptions.CheckpointRequiredException:
        return jsonify({"error": "Checkpoint required. Verify login manually."}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
