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