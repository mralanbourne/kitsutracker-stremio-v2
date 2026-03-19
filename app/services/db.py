import json
import logging
import copy
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from quart import current_app
from config import Config
from cachetools import TTLCache

logger = logging.getLogger(__name__)

headers = {"Authorization": f"Bearer {Config.UPSTASH_REDIS_REST_TOKEN}"}

# RAM-Cache: TTL reduced to 60s to prevent Split-Brain in Multi-Node-Setups
user_cache = TTLCache(maxsize=1000, ttl=60)

async def _redis_command(payload: list):
    """Führt generische Redis-Kommandos über die Upstash REST API aus (z.B. für Locks)."""
    url = f"{Config.UPSTASH_REDIS_REST_URL}/"
    client = current_app.httpx_client 
    try:
        resp = await client.post(url, headers=headers, json=payload, timeout=5.0)
        resp.raise_for_status()
        return resp.json().get("result")
    except Exception as e:
        logger.error(f"Upstash Generic Command Error: {e}")
        return None

async def _redis_request(method: str, endpoint: str, payload: str = None):
    url = f"{Config.UPSTASH_REDIS_REST_URL}/{endpoint}"
    client = current_app.httpx_client 
    try:
        if method == "GET":
            resp = await client.get(url, headers=headers, timeout=5.0)
        else:
            resp = await client.post(url, headers=headers, content=payload, timeout=5.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Upstash API Error on {endpoint}: {e}")
        return {}

async def acquire_lock(lock_key: str, expire_seconds: int = 15) -> bool:
    """Enterprise Distributed Lock via Redis SET NX EX."""
    result = await _redis_command(["SET", lock_key, "1", "NX", "EX", str(expire_seconds)])
    return result == "OK"

async def get_user(user_id: str) -> Optional[dict]:
    if user_id in user_cache:
        return copy.deepcopy(user_cache[user_id])
        
    res = await _redis_request("GET", f"get/user:{user_id}")
    data = res.get("result")

    if not data:
        return None
        
    try:
        user = json.loads(data)
        if "last_updated" in user and isinstance(user["last_updated"], str):
            user["last_updated"] = datetime.fromisoformat(user["last_updated"])
            
        user_cache[user_id] = copy.deepcopy(user)
        return user
    except Exception as e:
        logger.error(f"Error parsing user data for {user_id}: {e}")
        return None

async def store_user(user_details: dict, retries: int = 3) -> bool:
    """Speichert den Nutzer mit Guaranteed Write (Retry-Logik bei DB-Aussetzern)."""
    user_id = user_details.get("uid") or user_details.get("id")
    user_details["uid"] = user_id
    
    data_to_store = copy.deepcopy(user_details)
    if "last_updated" in data_to_store and isinstance(data_to_store["last_updated"], datetime):
         data_to_store["last_updated"] = data_to_store["last_updated"].isoformat()
    
    payload_string = json.dumps(data_to_store)
    
    for attempt in range(retries):
        res = await _redis_request("POST", f"set/user:{user_id}", payload=payload_string)
        if res.get("result") == "OK":
            user_cache[user_id] = copy.deepcopy(user_details)
            return True
        logger.warning(f"Upstash Write failed for {user_id}, attempt {attempt + 1}/{retries}")
        await asyncio.sleep(1 * (attempt + 1))
        
    logger.critical(f"FATAL: Could not store user {user_id} after {retries} attempts.")
    return False

async def update_user_progress(user: dict, anime_id: str, episode: int) -> bool:
    if not isinstance(user.get("progress"), dict):
        user["progress"] = {}
        
    user["progress"][str(anime_id)] = episode
    return await store_user(user)

async def get_valid_user(user_id: str) -> tuple[dict, Optional[str]]:
    user = await get_user(user_id)
    if not user:
        return {}, "No user found. Please re-login to Kitsu."
        
    if not all(user.get(k) for k in ["last_updated", "expires_in", "access_token", "refresh_token"]):
        return {}, "Invalid Kitsu session. Please log in again."

    expiration_date = user["last_updated"] + timedelta(seconds=user["expires_in"])
    
    # Auto-Refresh Kitsu Token with Distributed Locking
    if datetime.utcnow() > (expiration_date - timedelta(minutes=5)):
        lock_key = f"lock:refresh:{user_id}"
        
        # Try to get the exclusive lock
        if await acquire_lock(lock_key, expire_seconds=15):
            logger.info(f"Lock acquired. Refreshing token for user {user_id}.")
            from app.services.kitsu_client import KitsuClient
            try:
                tokens = await KitsuClient.refresh_token(user["refresh_token"])
                user["access_token"] = tokens["access_token"]
                user["refresh_token"] = tokens.get("refresh_token", user["refresh_token"])
                user["expires_in"] = tokens["expires_in"]
                user["last_updated"] = datetime.utcnow()
                
                success = await store_user(user)
                if success:
                    logger.info(f"Auto-refresh successful and saved for {user_id}.")
                else:
                    logger.error(f"Token refreshed but DB save failed for {user_id}.")
            except Exception as e:
                logger.error(f"Auto-refresh API call failed for {user_id}: {e}")
                return {}, "Kitsu session expired and refresh failed."
        else:
            logger.info(f"Refresh for {user_id} is locked by another process. Waiting...")
            await asyncio.sleep(2.0)
            user = await get_user(user_id)
            
    return user, None
