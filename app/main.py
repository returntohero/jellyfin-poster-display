import os
import time
import random
import json
from urllib.parse import urljoin
from flask import Flask, jsonify, request, Response, render_template
import requests

# --- CONFIGURATION ---
JELLYFIN_URL = os.environ.get("JELLYFIN_URL", "http://localhost:8096/")
JELLYFIN_TOKEN = os.environ.get("JELLYFIN_API_KEY") or os.environ.get("JELLYFIN_TOKEN")
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "2"))
IDLE_SWITCH_SECONDS = int(os.environ.get("IDLE_SWITCH_SECONDS", "15"))
CONFIG_PATH = os.environ.get("CONFIG_PATH", "config.json")

app = Flask(__name__, static_folder="static", template_folder="templates")

def jf_headers():
    h = {"Accept": "application/json"}
    if JELLYFIN_TOKEN:
        h["X-MediaBrowser-Token"] = JELLYFIN_TOKEN
    return h

def jellyfin_get(path, params=None, stream=False):
    url = urljoin(JELLYFIN_URL, path.lstrip("/"))
    return requests.get(url, headers=jf_headers(), params=params, stream=stream, timeout=10)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"library_ids": [], "include_tv": False}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def get_user():
    try:
        r = jellyfin_get("/Users")
        if r.status_code == 200:
            users = r.json()
            return users[0] if users else None
    except Exception:
        return None
    return None

def get_user_views(user_id):
    try:
        r = jellyfin_get(f"/Users/{user_id}/Views")
        if r.status_code == 200:
                return r.json().get("Items", [])
    except Exception:
        return []
    return []

def parse_position_seconds(sess):
    playstate = sess.get("PlayState") or {}
    ticks = playstate.get("PositionTicks")
    if ticks:
        try:
            return int(ticks) / 10_000_000
        except Exception:
            pass
    if "Position" in playstate:
        try:
            return float(playstate["Position"])
        except Exception:
            pass
    return None

@app.route("/")
def index():
    return render_template("index.html",
                           poll_interval=POLL_INTERVAL,
                           idle_switch_seconds=IDLE_SWITCH_SECONDS)

@app.route("/config", methods=["GET", "POST"])
def config_page():
    if request.method == "GET":
        cfg = load_config()
        user = get_user()
        if not user:
            return "Failed to get Jellyfin user (check JELLYFIN_URL/token)", 400
        views = get_user_views(user["Id"])
        return render_template("config.html", views=views, config=cfg)

    elif request.method == "POST":
        ids = request.form.getlist("library_ids")
        include_tv = request.form.get("include_tv") == "on"
        cfg = {"library_ids": ids, "include_tv": include_tv}
        save_config(cfg)
        return "Configuration saved! <a href='/config'>Back</a>"

@app.route("/api/now")
def api_now():
    try:
        r = jellyfin_get("/Sessions")
    except Exception as e:
        return jsonify({"error": "failed to reach jellyfin", "details": str(e)}), 502

    if r.status_code != 200:
        return jsonify({"error": "jellyfin returned %s" % r.status_code}), 502

    sessions = r.json() or []
    now_session = None
    for s in sessions:
        if s.get("NowPlayingItem"):
            now_session = s
            break

    if now_session:
        item = now_session["NowPlayingItem"]
        item_id = item.get("Id")
        title = item.get("Name") or item.get("OriginalTitle") or ""
        pos_seconds = parse_position_seconds(now_session)
        runtime_seconds = None
        if item.get("RunTimeTicks"):
            try:
                runtime_seconds = int(item["RunTimeTicks"]) / 10_000_000
            except Exception:
                runtime_seconds = None

        return jsonify({
            "playing": True,
            "title": title,
            "poster_item_id": item_id,
            "poster_url": f"/image/{item_id}?type=Primary",
            "position_seconds": pos_seconds,
            "runtime_seconds": runtime_seconds,
            "timestamp": int(time.time() * 1000)
        })

    cfg = load_config()
    ids = cfg.get("library_ids", [])
    include_tv = cfg.get("include_tv", False)

    types = ["Movie"]
    if include_tv:
        types.append("Series")

    params = {
        "IncludeItemTypes": ",".join(types),
        "Recursive": "true",
        "Fields": "RunTimeTicks",
        "Limit": 300
    }
    items = []
    for lid in ids or [None]:
        path = f"/Items" if lid is None else f"/Users/Public/Items?ParentId={lid}"
        try:
            r2 = jellyfin_get(path, params=params)
            if r2.status_code == 200:
                items.extend(r2.json().get("Items", []))
        except Exception:
            continue
    movies = [{"id": it["Id"], "title": it.get("Name")} for it in items if "Id" in it]
    return jsonify({
        "playing": False,
        "movies": movies,
        "timestamp": int(time.time() * 1000)
    })

@app.route("/image/<item_id>")
def proxy_image(item_id):
    img_type = request.args.get("type", "Primary")
    params = {}
    for k in ("maxWidth", "maxHeight", "minWidth", "quality"):
        v = request.args.get(k)
        if v:
            params[k] = v
    url_path = f"/Items/{item_id}/Images/{img_type}"
    try:
        rr = jellyfin_get(url_path, params=params, stream=True)
    except Exception as e:
        return jsonify({"error": "failed to contact jellyfin", "details": str(e)}), 502

    if rr.status_code != 200:
        return jsonify({"error": "jellyfin image returned %s" % rr.status_code}), rr.status_code

    return Response(rr.raw.read(), content_type=rr.headers.get("Content-Type", "image/jpeg"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
