from google.appengine.api import taskqueue
import json

from app.models import logger

def enqueue_task(target: str, queue_name: str, payload: dict):

    try:
        task = taskqueue.add(
            url=target,
            payload=json.dumps(payload),
            method='POST',
            queue_name=queue_name
        )

        logger.info(f"Enqueued task for {str(payload)}")
        return task
    except Exception:
        logger.error(f"Error enqueuing task for {str(payload)}")
        return None
