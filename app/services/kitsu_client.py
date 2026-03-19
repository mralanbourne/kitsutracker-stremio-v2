import logging
import asyncio
import json
from quart import current_app
from config import Config

logger = logging.getLogger(__name__)

class KitsuClient:
    KITSU_API_URL = "https://kitsu.io/api/edge"
    KITSU_OAUTH_URL = "https://kitsu.io/api/oauth/token"

    @staticmethod
    def _get_client():
        return current_app.httpx_client

    @classmethod
    async def _request_with_retry(cls, method: str, url: str, retries=3, **kwargs):
        """Führt Anfragen mit automatischer Wiederholung aus und parst JSON sicher."""
        client = cls._get_client()
        for attempt in range(retries):
            try:
                if method == "GET":
                    resp = await client.get(url, **kwargs)
                elif method == "POST":
                    resp = await client.post(url, **kwargs)
                elif method == "PATCH":
                    resp = await client.patch(url, **kwargs)
                
                resp.raise_for_status()
                
                # FIX: JSON Parsing innerhalb des Try-Blocks, damit kaputtes JSON Retry triggert!
                # Ausnahme: Wenn es ein 204 No Content ist, gibt es kein JSON
                if resp.status_code == 204:
                    return {}
                    
                return resp.json()
            except (Exception, json.JSONDecodeError) as e:
                if attempt == retries - 1:
                    logger.error(f"Kitsu API failed after {retries} attempts on {url}: {e}")
                    raise
                await asyncio.sleep(1 * (attempt + 1)) 

    @classmethod
    async def login(cls, username, password):
        payload = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": Config.KITSU_CLIENT_ID,
            "client_secret": Config.KITSU_CLIENT_SECRET
        }
        return await cls._request_with_retry("POST", cls.KITSU_OAUTH_URL, json=payload, timeout=5.0)

    @classmethod
    async def refresh_token(cls, refresh_token: str):
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": Config.KITSU_CLIENT_ID,
            "client_secret": Config.KITSU_CLIENT_SECRET
        }
        return await cls._request_with_retry("POST", cls.KITSU_OAUTH_URL, json=payload, timeout=5.0)

    @classmethod
    async def get_user_profile(cls, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        return await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/users?filter[self]=true", headers=headers, timeout=5.0)

    @classmethod
    async def get_anime(cls, anime_id: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        return await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/anime/{anime_id}", headers=headers, timeout=5.0)

    @classmethod
    async def search_library_entries(cls, user_id: str, anime_id: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        return await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/library-entries?filter[user_id]={user_id}&filter[anime_id]={anime_id}", headers=headers, timeout=5.0)

    @classmethod
    async def update_library_entry(cls, entry_id: str, progress: int, status: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json"}
        payload = {"data": {"id": entry_id, "type": "libraryEntries", "attributes": {"progress": progress, "status": status}}}
        return await cls._request_with_retry("PATCH", f"{cls.KITSU_API_URL}/library-entries/{entry_id}", headers=headers, json=payload, timeout=5.0)

    @classmethod
    async def create_library_entry(cls, user_id: str, anime_id: str, progress: int, status: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json"}
        payload = {"data": {"type": "libraryEntries", "attributes": {"progress": progress, "status": status}, "relationships": {"user": {"data": {"type": "users", "id": str(user_id)}}, "media": {"data": {"type": "anime", "id": str(anime_id)}}}}}
        return await cls._request_with_retry("POST", f"{cls.KITSU_API_URL}/library-entries", headers=headers, json=payload, timeout=5.0)

    @classmethod
    async def search_anime(cls, query: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        return await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/anime?filter[text]={query}&page[limit]=20", headers=headers, timeout=5.0)
        
    @classmethod
    async def get_library_catalog(cls, user_id: str, status: str, offset: int, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        return await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/library-entries?filter[user_id]={user_id}&filter[kind]=anime&filter[status]={status}&include=anime&page[limit]=20&page[offset]={offset}&sort=-updatedAt", headers=headers, timeout=5.0)
