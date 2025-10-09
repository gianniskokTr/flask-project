import logging
import json
from flask import request, jsonify
from app.tasks import bp as task_bp
from app.services.bigquery_service import log_item_consumed

logger = logging.getLogger(__name__)

@task_bp.route('/log_item_consumed', methods=['POST'])
def log_item_consumed_task():
    """
    Task handler for logging events to BigQuery.
    Called asynchronously by App Engine Task Queue.
    """
    task_name = request.headers.get('X-AppEngine-TaskName')
    if not task_name:
        logger.warning("Request not from task queue")
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = json.loads(request.data)

        user_id = data.get('user_id')
        item_id = data.get('item_id')
        store_id = data.get('store_id')
        timestamp = data.get('timestamp')

        if not all([user_id, item_id, store_id]):
            return jsonify({"error": "Missing required fields"}), 400

        # Log to BigQuery
        log_item_consumed(user_id, item_id, store_id, timestamp)
        logger.info(f"Successfully logged item consumption: user={user_id}, item={item_id}, store={store_id}, timestamp={timestamp}")

        return jsonify({"status": "success"}), 200

    except json.JSONDecodeError:
        logger.error("Invalid JSON in task payload")
        return jsonify({"error": "Invalid JSON"}), 400
