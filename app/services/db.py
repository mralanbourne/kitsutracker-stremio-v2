import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from quart import current_app
from config import Config
from cachetools import TTLCache

logger = logging.getLogger(__name__)

headers = {"Authorization": f"Bearer {Config.UPSTASH_REDIS_REST_TOKEN}"}

# RAM-Cache:
user_cache = TTLCache(maxsize=1000, ttl=300)

async def _redis_request(method: str, endpoint: str, payload: str = None):
    url = f"{Config.UPSTASH_REDIS_REST_URL}/{endpoint}"
    client = current_app.httpx_client 
    
    try:
        if method == "GET":
            resp = await client.get(url, headers=headers)
        else:
            resp = await client.post(url, headers=headers, content=payload)
            
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Upstash API Error: {e}")
        return {}

async def get_user(user_id: str) -> Optional[dict]:
    
    if user_id in user_cache:
       
        return user_cache[user_id].copy()
        
    
    res = await _redis_request("GET", f"get/user:{user_id}")
    data = res.get("result")

    if not data:
        return None
        
    try:
        user = json.loads(data)

        if "last_updated" in user and isinstance(user["last_updated"], str):
            user["last_updated"] = datetime.fromisoformat(user["last_updated"])
            
        
        user_cache[user_id] = user.copy()
        
        return user
    except Exception as e:
        logger.error(f"Error when trying to parse user data: {e}")
        return None

async def store_user(user_details: dict) -> bool:
    user_id = user_details.get("uid") or user_details.get("id")
    user_details["uid"] = user_id
    
    data_to_store = user_details.copy()
    
    if "last_updated" in data_to_store and isinstance(data_to_store["last_updated"], datetime):
         data_to_store["last_updated"] = data_to_store["last_updated"].isoformat()
    
    payload_string = json.dumps(data_to_store)
    
    res = await _redis_request("POST", f"set/user:{user_id}", payload=payload_string)
    success = res.get("result") == "OK"
    
    if success:
        user_cache[user_id] = user_details.copy()
        
    return success

async def update_user_progress(user: dict, anime_id: str, episode: int):
    if "progress" not in user:
        user["progress"] = {}
        
    user["progress"][str(anime_id)] = episode
    await store_user(user)

async def get_valid_user(user_id: str) -> tuple[dict, Optional[str]]:
    user = await get_user(user_id)
    if not user:
        return {}, "No user found. Please re-login to Kitsu."
        
    if not all(user.get(k) for k in ["last_updated", "expires_in", "access_token", "refresh_token"]):
        return {}, "Invalid Kitsu session. Please log in again."

    expiration_date = user["last_updated"] + timedelta(seconds=user["expires_in"])
    
    # Auto-Refresh Kitsu Token:
    if datetime.utcnow() > (expiration_date - timedelta(minutes=5)):
        logger.info(f"Token expired or expiring soon for user {user_id}. Attempting auto-refresh.")
        from app.services.kitsu_client import KitsuClient
        try:
            tokens = await KitsuClient.refresh_token(user["refresh_token"])
            user["access_token"] = tokens["access_token"]
            user["refresh_token"] = tokens.get("refresh_token", user["refresh_token"])
            user["expires_in"] = tokens["expires_in"]
            user["last_updated"] = datetime.utcnow()
            await store_user(user)
            logger.info(f"Auto-refresh successful for user {user_id}.")
        except Exception as e:
            logger.error(f"Auto-refresh failed for user {user_id}: {e}")
            return {}, "Kitsu session expired and refresh failed. Please log in again."
            
    return user, None
