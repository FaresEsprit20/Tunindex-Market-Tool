# config.py

# -------------------------
# ACTIVE PROVIDER
# -------------------------
ACTIVE_PROVIDER = "ilboursa"   # ilboursa | bvmt | tunisie_valeurs

# -------------------------
# DATABASE
# -------------------------
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "root"
DB_NAME = "tunindex"

# -------------------------
# SCRAPING SETTINGS
# -------------------------
USE_PROXY = False
USE_BROWSER = True

REQUEST_TIMEOUT = 10
RETRY_COUNT = 3
RATE_LIMIT_DELAY = 1.5

# -------------------------
# CACHE
# -------------------------
CACHE_TTL = 3600  # seconds

# -------------------------
# PARALLELISM
# -------------------------
MAX_WORKERS = 5

DETAIL_SCRAPE_LIMIT = 20