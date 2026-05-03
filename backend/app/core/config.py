from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "reconciliation.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

UPLOADS_DIR = PROJECT_ROOT / "uploads"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"

SAMPLE_RETAIL_DIR = PROJECT_ROOT / "sample_data" / "retail"
PRODUCT_CATALOG_PATH = SAMPLE_RETAIL_DIR / "product_catalog.csv"
