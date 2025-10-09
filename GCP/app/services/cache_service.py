from google.appengine.api import memcache
from google.cloud import bigquery
import datetime

from app.models import logger

PROJECT_ID = "acquired-ripple-473314-j5"
DATASET_ID = "flask_project_dataser"
TABLE_ID = "ItemsConsumed"

bq_client = bigquery.Client(project=PROJECT_ID)

CACHE_KEY = "cached_analytics"

# def fetch_events_from_bq(limit: int =20):
#     query = f"""
#         SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
#         ORDER BY timestamp DESC
#         LIMIT {limit}
#     """
#     results = list(bq_client.query(query))
#     return [dict(row) for row in results]
#
#
# def get_cached_events():
#     events = memcache.get(CACHE_KEY)
#     if not events: #fallback if cache not yet initiated
#         events = fetch_events_from_bq()
#         memcache.set(CACHE_KEY, events, time=6*3600)
#     return events


def fetch_analytics_from_bq():
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    queries = {
        'recent_users': f"""
            SELECT DISTINCT user_id
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            WHERE timestamp >= '{seven_days_ago}'
        """,
        'store_sales': f"""
            SELECT 
                store_id,
                ARRAY_AGG(STRUCT(
                    item_id,
                    total_items_sold
                ) ORDER BY total_items_sold DESC) as items
            FROM (
                SELECT 
                    store_id,
                    item_id,
                    COUNT(*) as total_items_sold
                FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
                WHERE timestamp >= '{seven_days_ago}'
                GROUP BY store_id, item_id
            )
            GROUP BY store_id
            ORDER BY store_id
        """,
        'user_purchases': f"""
            SELECT 
                user_id,
                ARRAY_AGG(STRUCT(
                    item_id,
                    total_items_bought
                ) ORDER BY total_items_bought DESC) as items
            FROM (
                SELECT 
                    user_id,
                    item_id,
                    COUNT(*) as total_items_bought
                FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
                WHERE timestamp >= '{seven_days_ago}'
                GROUP BY user_id, item_id
            )
            GROUP BY user_id
            ORDER BY user_id
        """
    }

    results = {}
    jobs = {}

    for name, query in queries.items():
        query_job = bq_client.query(query)
        jobs[name] = query_job

    for name, job in jobs.items():
        rows = job.result()
        results[name] = [dict(row) for row in rows]

    return results


def get_cached_analytics():
    analytics = memcache.get(CACHE_KEY)
    if not analytics: #fallback if cache not yet initiated
        analytics = fetch_analytics_from_bq()
        memcache.set(CACHE_KEY, analytics, time=3600*24)
    return analytics


