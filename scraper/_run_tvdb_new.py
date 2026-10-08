"""Run TVDB episode ingest for new TV titles added by recent global ingest."""
import sys, sqlite3, os
sys.path.insert(0, '.')
from dotenv import dotenv_values
ENV = dotenv_values('.env')
for k, v in ENV.items():
    if v is not None and k not in os.environ:
        os.environ[k] = v
import tvdb_episode_ingest

# Override the row query to target new TV titles only (id > 110050), no seasons
# We monkey-patch by passing our own db_path but the existing run() queries
# "type='tv' AND id NOT IN (SELECT DISTINCT title_id FROM seasons)" which
# already picks up new titles without seasons. Limit 2000 to bound runtime.

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

print("Starting TVDB episode ingest (limit=2000)...")
result = tvdb_episode_ingest.run(db_path='catalog.db', limit=2000, refresh_existing=False)
print("RESULT:", result)