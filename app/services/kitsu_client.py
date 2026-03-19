import logging
import asyncio
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
        """Führt Anfragen mit automatischer Wiederholung (Retry-Logic) aus."""
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
                return resp
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Kitsu API failed after {retries} attempts: {e}")
                    raise
                # Exponentielles Backoff: wartet 1s, dann 2s vor dem nächsten Versuch
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
        resp = await cls._request_with_retry("POST", cls.KITSU_OAUTH_URL, json=payload, timeout=5.0)
        return resp.json()

    @classmethod
    async def refresh_token(cls, refresh_token: str):
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": Config.KITSU_CLIENT_ID,
            "client_secret": Config.KITSU_CLIENT_SECRET
        }
        resp = await cls._request_with_retry("POST", cls.KITSU_OAUTH_URL, json=payload, timeout=5.0)
        return resp.json()

    @classmethod
    async def get_user_profile(cls, access_token: str):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.api+json"
        }
        resp = await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/users?filter[self]=true", headers=headers, timeout=5.0)
        return resp.json()

    @classmethod
    async def get_anime(cls, anime_id: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        resp = await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/anime/{anime_id}", headers=headers, timeout=5.0)
        return resp.json()

    @classmethod
    async def search_library_entries(cls, user_id: str, anime_id: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        resp = await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/library-entries?filter[user_id]={user_id}&filter[anime_id]={anime_id}", headers=headers, timeout=5.0)
        return resp.json()

    @classmethod
    async def update_library_entry(cls, entry_id: str, progress: int, status: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json"}
        payload = {"data": {"id": entry_id, "type": "libraryEntries", "attributes": {"progress": progress, "status": status}}}
        resp = await cls._request_with_retry("PATCH", f"{cls.KITSU_API_URL}/library-entries/{entry_id}", headers=headers, json=payload, timeout=5.0)
        return resp.json()

    @classmethod
    async def create_library_entry(cls, user_id: str, anime_id: str, progress: int, status: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json"}
        payload = {"data": {"type": "libraryEntries", "attributes": {"progress": progress, "status": status}, "relationships": {"user": {"data": {"type": "users", "id": str(user_id)}}, "media": {"data": {"type": "anime", "id": str(anime_id)}}}}}
        resp = await cls._request_with_retry("POST", f"{cls.KITSU_API_URL}/library-entries", headers=headers, json=payload, timeout=5.0)
        return resp.json()

    @classmethod
    async def search_anime(cls, query: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        resp = await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/anime?filter[text]={query}&page[limit]=20", headers=headers, timeout=5.0)
        return resp.json()
        
    @classmethod
    async def get_library_catalog(cls, user_id: str, status: str, offset: int, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.api+json"}
        resp = await cls._request_with_retry("GET", f"{cls.KITSU_API_URL}/library-entries?filter[user_id]={user_id}&filter[kind]=anime&filter[status]={status}&include=anime&page[limit]=20&page[offset]={offset}&sort=-updatedAt", headers=headers, timeout=5.0)
        return resp.json()
