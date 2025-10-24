import os
import requests
from flask import Flask, jsonify, render_template
from datetime import datetime, timedelta

app = Flask(__name__)

JELLYFIN_URL = os.getenv("JELLYFIN_URL", "http://jellyfin:8096")
API_KEY = os.getenv("JELLYFIN_API_KEY", "")
USER_ID = os.getenv("JELLYFIN_USER_ID", "")

headers = {
    "X-Emby-Token": API_KEY
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/now")
def now_playing():
    try:
        sessions = requests.get(f"{JELLYFIN_URL}/Sessions", headers=headers, timeout=5).json()
        for session in sessions:
            if "NowPlayingItem" in session:
                item = session["NowPlayingItem"]
                playback = session.get("PlayState", {})
                duration = item.get("RunTimeTicks", 0) / 10000000
                position = playback.get("PositionTicks", 0) / 10000000
                end_time = datetime.now() + timedelta(seconds=(duration - position))

                return jsonify({
                    "title": item.get("Name", "Unknown Title"),
                    "poster": f"{JELLYFIN_URL}/Items/{item['Id']}/Images/Primary?api_key={API_KEY}",
                    "duration": duration,
                    "position": position,
                    "end_time": end_time.strftime("%H:%M"),
                    "start_time": (datetime.now() - timedelta(seconds=position)).strftime("%H:%M")
                })
        return jsonify({"title": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/library")
def get_library():
    try:
        items = requests.get(
            f"{JELLYFIN_URL}/Users/{USER_ID}/Items?IncludeItemTypes=Movie&Recursive=true",
            headers=headers,
            timeout=5
        ).json()
        posters = [
            f"{JELLYFIN_URL}/Items/{item['Id']}/Images/Primary?api_key={API_KEY}"
            for item in items.get("Items", [])
        ]
        return jsonify(posters)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
