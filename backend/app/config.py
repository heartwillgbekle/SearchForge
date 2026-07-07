import os
from pathlib import Path

# backend/app/
APP_DIR = Path(__file__).resolve().parent

DOCUMENTS_DIR = APP_DIR / "data" / "documents"
DATABASE_PATH = APP_DIR / "data" / "searchforge.db"

# --- Redis cache -----------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

# How long a cached search response stays valid. Short enough that stale
# results self-correct once documents change.
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))  # 5 min

# Dev convenience: when no Redis server is available, set USE_FAKE_REDIS=1
# to use an in-process fake so caching still works locally. Never enable
# this in production.
USE_FAKE_REDIS = os.environ.get("USE_FAKE_REDIS", "0") == "1"
