import logging
from quart import Blueprint
from app.services.db import get_valid_user, update_user_progress
from app.services.kitsu_client import KitsuClient
from .utils import respond_with

content_sync_bp = Blueprint("content_sync", __name__)
logger = logging.getLogger(__name__)

@content_sync_bp.route("/<auth_id>/subtitles/<catalog_type>/<stremio_id>.json")
@content_sync_bp.route("/<auth_id>/subtitles/<catalog_type>/<stremio_id>/<path:extra>.json")
async def sync_progress(auth_id: str, catalog_type: str, stremio_id: str, extra: str = ""):
    vtt_content = "WEBVTT\n\n00:00:00.000 --> 00:00:04.000\nKitsu: Sync sent"
    dummy_sub = {"subtitles": [{"id": "kitsu-sync-status", "url": f"data:text/vtt;charset=utf-8,{vtt_content}", "lang": "Kitsu Sync Info"}]}
    cache_config = {"cache_max_age": 300, "stale_revalidate": 600}

    if not stremio_id.startswith("kitsu:"):
        return await respond_with(dummy_sub, **cache_config)

    parts = stremio_id.split(":")
    anime_id = parts[1]
    try:
        episode = int(parts[3]) if len(parts) >= 4 else int(parts[2]) if len(parts) == 3 else 1
    except (ValueError, IndexError):
        episode = 1

    user, error = await get_valid_user(auth_id)
    if error or not user:
        return await respond_with(dummy_sub, **cache_config)

    if episode <= user.get("progress", {}).get(anime_id, 0):
        return await respond_with(dummy_sub, **cache_config)

    access_token = user.get("access_token")

    try:
        # Check Total Episodes
        anime_data = await KitsuClient.get_anime(anime_id, access_token)
        total_episodes = anime_data.get("data", {}).get("attributes", {}).get("episodeCount")
        
        target_status = "completed" if total_episodes and episode >= total_episodes else "current"

        # Search library entry
        search_data = await KitsuClient.search_library_entries(user.get("id"), anime_id, access_token)
        entries = search_data.get("data", [])

        if entries:
            entry_id = entries[0]["id"]
            await KitsuClient.update_library_entry(entry_id, episode, target_status, access_token)
        else:
            await KitsuClient.create_library_entry(user.get("id"), anime_id, episode, target_status, access_token)

        await update_user_progress(auth_id, anime_id, episode)
        logger.info(f"Progress synced: {auth_id} | Anime {anime_id} | Ep {episode}")

    except Exception as e:
        logger.error(f"Sync Error for {auth_id}: {e}")

    return await respond_with(dummy_sub, **cache_config)
