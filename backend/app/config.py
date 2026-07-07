from pathlib import Path

# backend/app/
APP_DIR = Path(__file__).resolve().parent

DOCUMENTS_DIR = APP_DIR / "data" / "documents"
DATABASE_PATH = APP_DIR / "data" / "searchforge.db"
