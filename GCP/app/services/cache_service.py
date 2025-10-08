from google.appengine.api import memcache
from google.cloud import bigquery

PROJECT_ID = "acquired-ripple-473314-j5"
DATASET_ID = "flask_project_dataser"
TABLE_ID = "ItemsConsumed"

bq_client = bigquery.Client(project=PROJECT_ID)

CACHE_KEY = "items_consumed"

def fetch_events_from_bq(limit: int =20):
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    results = list(bq_client.query(query))
    return [dict(row) for row in results]


def get_cached_events():
    events = memcache.get(CACHE_KEY)
    if not events: #fallback if cache not yet initiated
        events = fetch_events_from_bq()
        memcache.set(CACHE_KEY, events, time=6*3600)
    return events
