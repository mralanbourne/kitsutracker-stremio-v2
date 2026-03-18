import logging
from quart import Blueprint, current_app
from app.services.db import get_valid_user, update_user_progress
from .utils import respond_with

content_sync_bp = Blueprint("content_sync", __name__)
logger = logging.getLogger(__name__)
KITSU_API_URL = "https://kitsu.io/api/edge"

def get_kitsu_headers(access_token: str):
    return {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {access_token}"
    }

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

    client = current_app.httpx_client
    headers = get_kitsu_headers(user.get("access_token"))

    try:
        # Check Total Episodes
        anime_resp = await client.get(f"{KITSU_API_URL}/anime/{anime_id}", headers=headers, timeout=5.0)
        total_episodes = None
        if anime_resp.status_code == 200:
            total_episodes = anime_resp.json().get("data", {}).get("attributes", {}).get("episodeCount")
        
        target_status = "completed" if total_episodes and episode >= total_episodes else "current"

        # Search library entry
        search_resp = await client.get(f"{KITSU_API_URL}/library-entries?filter[user_id]={user.get('id')}&filter[anime_id]={anime_id}", headers=headers, timeout=5.0)
        search_resp.raise_for_status()
        entries = search_resp.json().get("data", [])

        if entries:
            entry_id = entries[0]["id"]
            payload = {"data": {"id": entry_id, "type": "libraryEntries", "attributes": {"progress": episode, "status": target_status}}}
            await client.patch(f"{KITSU_API_URL}/library-entries/{entry_id}", headers=headers, json=payload, timeout=5.0)
        else:
            payload = {"data": {"type": "libraryEntries", "attributes": {"progress": episode, "status": target_status}, "relationships": {"user": {"data": {"type": "users", "id": str(user.get('id'))}}, "media": {"data": {"type": "anime", "id": str(anime_id)}}}}}
            await client.post(f"{KITSU_API_URL}/library-entries", headers=headers, json=payload, timeout=5.0)

        await update_user_progress(auth_id, anime_id, episode)
        logger.info(f"Progress synced: {auth_id} | Anime {anime_id} | Ep {episode}")

    except Exception as e:
        logger.error(f"Sync Error for {auth_id}: {e}")

    return await respond_with(dummy_sub, **cache_config)
