import os
from datetime import timedelta
from dotenv import load_dotenv

#===============
# Load environment variables from a ".env" file
# This is crucial for local development to keep secrets safe
#===============
load_dotenv()

class Config:
    #===============
    # Disable automatic alphabetical sorting of JSON keys
    # This preserves the original order of dictionaries
    #===============
    JSON_SORT_KEYS = False
    
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("CRITICAL ERROR: SECRET_KEY environment variable is not set!")
    
    #===============
    # Define how long a permanent user session lasts
    # Here it is set to 30 days before requiring a completely new login
    #===============
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
    UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
        raise ValueError("CRITICAL ERROR: Upstash credentials missing!")
    
    KITSU_CLIENT_ID = os.getenv("KITSU_CLIENT_ID")
    KITSU_CLIENT_SECRET = os.getenv("KITSU_CLIENT_SECRET")
    if not KITSU_CLIENT_ID or not KITSU_CLIENT_SECRET:
        raise ValueError("CRITICAL ERROR: Kitsu credentials missing!")
    
    #===============
    # Cache Configuration Constants
    # Defines how long Stremio should cache the responses
    #===============
    DEFAULT_STALE_WHILE_REVALIDATE = 600  
    MANIFEST_DURATION = 3600
