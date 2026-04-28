import logging
import base64
from quart import Blueprint
from app.services.db import get_valid_user, update_user_progress
from app.services.kitsu_client import KitsuClient
from .utils import respond_with

content_sync_bp = Blueprint("content_sync", __name__)
logger = logging.getLogger(__name__)

@content_sync_bp.route("/<auth_id>/subtitles/<catalog_type>/<stremio_id>.json")
@content_sync_bp.route("/<auth_id>/subtitles/<catalog_type>/<stremio_id>/<path:extra>.json")
async def sync_progress(auth_id: str, catalog_type: str, stremio_id: str, extra: str = ""):
    #===============
    # Stremio queries subtitle tracks at runtime when a user presses play.
    # We deliver a "dummy" WebVTT subtitle object back while running the Kitsu sync asynchronously.
    #===============
    vtt_content = "WEBVTT\n\n00:00:00.000 --> 00:00:04.000\nKitsu: Sync sent"
    vtt_b64 = base64.b64encode(vtt_content.encode("utf-8")).decode("utf-8")
    
    dummy_sub = {"subtitles": [{"id": "kitsu-sync-status", "url": f"data:text/vtt;base64,{vtt_b64}", "lang": "Kitsu Sync Info"}]}
    cache_config = {"cache_max_age": 300, "stale_revalidate": 600}

    if not stremio_id.startswith("kitsu:"):
        return await respond_with(dummy_sub, **cache_config)

    parts = stremio_id.split(":")
    anime_id = parts[1]
    
    # Extract precise episode integer regardless of stremio format
    try:
        episode = int(parts[3]) if len(parts) >= 4 else int(parts[2]) if len(parts) == 3 else 1
    except (ValueError, IndexError):
        episode = 1

    user, error = await get_valid_user(auth_id)
    if error or not user:
        return await respond_with(dummy_sub, **cache_config)

    user_progress = user.get("progress") or {}
    
    # Avoid duplicate calls to API if user restarts the same episode
    if episode <= user_progress.get(anime_id, 0):
        return await respond_with(dummy_sub, **cache_config)

    access_token = user.get("access_token")
    user_internal_id = user.get("id")

    try:
        #===============
        # First query anime data to ensure we correctly move it to "completed" if it's the final episode
        #===============
        anime_data = await KitsuClient.get_anime(anime_id, access_token)
        total_episodes = anime_data.get("data", {}).get("attributes", {}).get("episodeCount")
        
        target_status = "completed" if total_episodes and episode >= total_episodes else "current"

        search_data = await KitsuClient.search_library_entries(user_internal_id, anime_id, access_token)
        entries = search_data.get("data", [])

        if entries:
            entry_id = entries[0]["id"]
            await KitsuClient.update_library_entry(entry_id, episode, target_status, access_token)
        else:
            try:
                await KitsuClient.create_library_entry(user_internal_id, anime_id, episode, target_status, access_token)
            except Exception as e:
                logger.warning(f"Could not create entry for {user_internal_id} (possible Stremio double-fire): {e}")

        write_success = await update_user_progress(user, anime_id, episode)
        
        if write_success:
            logger.info(f"Progress synced & saved: {auth_id} | Anime {anime_id} | Ep {episode}")
        else:
            logger.critical(f"DATA LOSS RISK: API synced but Upstash DB write failed for {auth_id} | Anime {anime_id}")

    except Exception as e:
        logger.error(f"Sync Error for {auth_id}: {e}")

    return await respond_with(dummy_sub, **cache_config)
