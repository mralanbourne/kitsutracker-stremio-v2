from typing import Any
from quart import Blueprint
from config import Config
from app.services.db import get_user
from app.routes.utils import respond_with

manifest_blueprint = Blueprint("manifest", __name__)

genres = ["Action", "Adventure", "Comedy", "Drama", "Fantasy", "Horror", "Mecha", "Music", "Mystery", "Psychological", "Romance", "Sci-Fi", "Slice of Life", "Sports", "Supernatural", "Thriller"]

MANIFEST: dict[str, Any] = {
    "id": "org.kitsu-stremio-sync",
    "version": "3.0.0",
    "name": "Kitsu Tracker",
    "description": "Your ultimate Kitsu anime catalog and watch-tracker for Stremio.",
    "logo": "https://kitsutracker.koyeb.app/static/fox_small.png",
    "types": ["anime", "series", "movie"],
    "catalogs": [
        {
            "type": "anime",
            "id": "current",
            "name": "Kitsu: Currently Watching",
            "extra": [{"name": "skip"}, {"name": "genre", "options": genres}]
        },
        {
            "type": "anime",
            "id": "planned",
            "name": "Kitsu: Want to Watch",
            "extra": [{"name": "skip"}, {"name": "genre", "options": genres}]
        },
        {
            "type": "anime",
            "id": "completed",
            "name": "Kitsu: Completed",
            "extra": [{"name": "skip"}, {"name": "genre", "options": genres}]
        },
        {
            "type": "anime",
            "id": "on_hold",
            "name": "Kitsu: On Hold",
            "extra": [{"name": "skip"}, {"name": "genre", "options": genres}]
        },
        {
            "type": "anime",
            "id": "dropped",
            "name": "Kitsu: Dropped",
            "extra": [{"name": "skip"}, {"name": "genre", "options": genres}]
        },
        {
            "type": "anime",
            "id": "kitsu_search",
            "name": "Kitsu: Search",
            "extra": [{"name": "search", "isRequired": True}]
        }
    ],
    "behaviorHints": {"configurable": True},
    "resources": ["catalog", "subtitles"], 
    

    "idPrefixes": ["kitsu"]
}

@manifest_blueprint.route("/manifest.json", methods=["GET", "OPTIONS"])
async def addon_unconfigured_manifest():
    unconfigured_manifest = MANIFEST.copy()
    unconfigured_manifest["behaviorHints"] = {
        "configurable": True,
        "configurationRequired": True,
    }
    return await respond_with(
        unconfigured_manifest,
        cache_max_age=Config.MANIFEST_DURATION,
        stale_revalidate=Config.DEFAULT_STALE_WHILE_REVALIDATE,
        stremio_response=False, 
    )

@manifest_blueprint.route("/<user_id>/manifest.json", methods=["GET", "OPTIONS"])
async def addon_configured_manifest(user_id: str):
    user = await get_user(user_id)
    if not user:
        return await respond_with({"error": "User not found"}, private=True, cache_max_age=1800)
    
    user_manifest = MANIFEST.copy()
    user_catalogs = user.get("catalogs")

    if user_catalogs is not None:
        filtered_catalogs = [cat for cat in user_manifest["catalogs"] if cat["id"] in user_catalogs or cat["id"] == "kitsu_search"]
        user_manifest["catalogs"] = filtered_catalogs

    return await respond_with(
        user_manifest, 
        stremio_response=False,
        cache_max_age=Config.MANIFEST_DURATION, 
        stale_revalidate=Config.DEFAULT_STALE_WHILE_REVALIDATE
    )
