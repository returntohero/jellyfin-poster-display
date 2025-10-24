# 🎬 Jellyfin Poster Display

A simple Dockerized Flask app that connects to your Jellyfin server and displays large, cinema-style posters:
- Shows **Now Playing** poster and runtime when something is playing.
- When idle, cycles posters from selected libraries (movies and optionally TV shows).
- Configuration UI to choose which libraries and whether to include TV shows.
- Smooth cross-fade transitions between posters.

## Quickstart (Docker)

1. Clone this repo:
```bash
git clone https://github.com/yourusername/jellyfin-poster-display.git
cd jellyfin-poster-display
```
2. Edit `docker-compose.yml` to set your `JELLYFIN_URL` and `JELLYFIN_API_KEY`.
3. (Optional) Persist config by editing or creating `config.json` in the project root.
4. Build & run:
```bash
docker compose up -d --build
```
5. Open the display at `http://<host>:8000/`.
6. Configure libraries at `http://<host>:8000/config`.

## Environment variables
- `JELLYFIN_URL` — Jellyfin base URL (e.g., http://192.168.1.25:8096/)
- `JELLYFIN_API_KEY` — Jellyfin user token (X-MediaBrowser-Token)
- `POLL_INTERVAL` — seconds between polling `/Sessions` (default 2)
- `IDLE_SWITCH_SECONDS` — seconds between posters in idle mode (default 15)

## Author & License
**Author:** Jeff P  
**License:** MIT — see `LICENSE` for details.
