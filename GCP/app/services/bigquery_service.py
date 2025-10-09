from google.cloud import bigquery
import uuid
import datetime

from app.models import logger

PROJECT_ID = "acquired-ripple-473314-j5"
DATASET_ID = "flask_project_dataser"
TABLE_ID = "ItemsConsumed"

bq_client = bigquery.Client(project=PROJECT_ID)

def log_item_consumed(user_id: int, store_id: int, item_id: int, timestamp: datetime.datetime):
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    row = {
        "timestamp": timestamp,
        "user_id": user_id,
        "store_id": store_id,
        "item_id": item_id,
        "event_id": uuid.uuid4().int >> 96
    }

    errors = bq_client.insert_rows_json(table_ref, [row])
    if errors:
        logger.error(f"Error inserting row into BigQuery: {errors}")

def fetch_analytics_from_bq():
    """
        Fetches analytics data from BigQuery and returns it in a dictionary format.

        This function uses three separate BigQuery jobs to fetch the following data:
        - A list of distinct user IDs from the last 7 days
        - A list of stores along with the items they have sold in the last 7 days
        - A list of users along with the items they have purchased in the last 7 days

        The results are returned in a dictionary format, with each key being a string representing the type of data, and the value being a list of dictionaries containing the data.

        The dictionaries for the store sales and user purchases will contain the following keys:
        - 'store_id' or 'user_id'
        - 'items' - a list of dictionaries containing the following keys:
          - 'item_id'
          - 'total_items_sold' or 'total_items_bought'

        The dictionary for the recent users will contain the following key:
        - 'user_id'

        The data is fetched from the last 7 days.

        Returns:
            dict: a dictionary containing the analytics data
    """
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
