import hashlib
import logging
import time
from quart import Blueprint, flash, make_response, redirect, render_template, request, session, url_for, current_app
from app.services.db import get_user, store_user

ui_bp = Blueprint("ui", __name__)
logger = logging.getLogger(__name__)

# Global In-Memory Cache for Kitsu Status
_kitsu_status_cache = {"status": "offline", "timestamp": 0}
CACHE_TTL = 60

@ui_bp.route("/")
async def index():
    if session.get("user"):
        return redirect(url_for("ui.configure"))
    return await render_template("index.html")

@ui_bp.route("/health")
async def health_check():
    return {"status": "alive", "message": "Koyeb, don't you dare sleep."}, 200

@ui_bp.route("/kitsu-status")
async def kitsu_status():
    current_time = time.time()
    
    # 1. Check:
    if current_time - _kitsu_status_cache["timestamp"] < CACHE_TTL:
        status = _kitsu_status_cache["status"]
        return {"status": status}, 200 if status == "online" else 503

    # 2. Request new data:
    client = current_app.httpx_client
    try:
        resp = await client.get("https://kitsu.io/api/edge/anime?page[limit]=1", timeout=3.0)
        
        if resp.status_code == 200:
            _kitsu_status_cache["status"] = "online"
            _kitsu_status_cache["timestamp"] = current_time
            return {"status": "online"}, 200
            
        _kitsu_status_cache["status"] = "offline"
        _kitsu_status_cache["timestamp"] = current_time
        return {"status": "offline"}, 503
        
    except Exception:
        _kitsu_status_cache["status"] = "offline"
        _kitsu_status_cache["timestamp"] = current_time
        return {"status": "offline"}, 503

@ui_bp.route("/config")
async def stremio_config():
    return await render_template("index.html")

@ui_bp.route("/configure", methods=["GET", "POST"])
@ui_bp.route("/<user_id>/configure", methods=["GET", "POST"])
async def configure(user_id: str = ""):
    if not (user_session := session.get("user")):
        return await render_template("index.html")
    
    user = await get_user(user_session["uid"])
    if not user:
        session.pop("user", None)
        return redirect(url_for("ui.index"))

    if request.method == "POST":
        form = await request.form
        user["catalogs"] = [k.replace("include_", "") for k, v in form.items() if k.startswith("include_")]
        await store_user(user)
        await flash("Saved! Re-install the addon to apply layout changes.", "success")

    cats = user.get("catalogs", [])
    config_hash = hashlib.md5("".join(sorted(cats)).encode()).hexdigest()[:8] if cats else "new"
    
    domain = request.host
    manifest_url = f"https://{domain}/{user['uid']}/manifest.json?v={config_hash}"
    manifest_magnet = manifest_url.replace("https://", "stremio://")

    return await render_template(
        "configure.html", 
        user=user, 
        manifest_url=manifest_url, 
        manifest_magnet=manifest_magnet
    )
