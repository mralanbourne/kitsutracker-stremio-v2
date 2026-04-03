import os
import httpx
import logging
from quart import Quart
from quart_cors import cors
from config import Config

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")

    app = Quart(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    # CORS Setup
    app = cors(app, allow_origin="*")

    @app.before_serving
    async def create_client():
        logger.info("Initializing global HTTPX AsyncClient")
        app.httpx_client = httpx.AsyncClient()

    @app.after_serving
    async def close_client():
        logger.info("Closing global HTTPX AsyncClient")
        await app.httpx_client.aclose()

    from app.routes.ui import ui_bp
    from app.routes.auth import auth_blueprint
    from app.routes.manifest import manifest_blueprint
    from app.routes.catalog import catalog_bp
    from app.routes.content_sync import content_sync_bp

    app.register_blueprint(ui_bp)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(manifest_blueprint)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(content_sync_bp)

    return app
