from google.appengine.api import taskqueue
import json

from app.models import logger

def enqueue_task(**kwargs):
    user_id = kwargs.get("user_id")
    item_id = kwargs.get("item_id")
    store_id = kwargs.get("store_id")
    timestamp = kwargs.get("timestamp")

    try:
        payload = json.dumps({
            'user_id': user_id,
            'item_id': item_id,
            'store_id': store_id,
            'timestamp': timestamp
        })

        task = taskqueue.add(
            url='/tasks/log_item_consumed',
            payload=payload,
            method='POST',
            queue_name='log-item-consumed'
        )

        logger.info(f"Enqueued task for item {item_id} consumed by user {user_id} in store {store_id} at {timestamp}")
        return task
    except Exception as e:
        logger.error(f"Error enqueuing task for item {item_id} consumed by user {user_id} in store {store_id}: {e} at {timestamp}")
        return None
