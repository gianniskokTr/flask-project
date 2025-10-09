from flask import jsonify, request
from google.appengine.ext import ndb
from flask_login import login_required, current_user
import datetime

from app.models import StoreModel, ItemModel, logger
from app.core import bp
from app.exceptions import (
    ItemNotFoundError,
    ItemSoldOutError,
    StoreNotFoundError,
    InvalidItemQuantity,
    InvalidItemPrice
)
from app.decorators import admin_required

from app.services.cache_service import get_cached_events
from app.services.task_service import enqueue_task

@bp.route("/stores", methods=["POST"])
@login_required
@admin_required
def create_store():
    """
        Create a new store with the provided data.

        Request Body:
            JSON object containing store attributes. 'name' is required.

        Returns:
            Response object with the store's key details in JSON format and an HTTP status code 201 on success.
            Returns an error message in JSON format with an HTTP status code 400 for invalid input.

        Example:
            Request:
                POST /stores
                {
                    "name": "New Store",
                    "description": "A new store"
                }
            Response:
                201 Created
                {
                    "model": "StoreModel",
                    "key_id": 12345
                }
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": 'Invalid JSON'}), 400

    try:
        store = StoreModel(**data)
        key = store.put()
        return jsonify({"model": key.kind(), "key_id": key.id()}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 400


@bp.route("/stores/<int:store_id>", methods=['GET'])
@login_required
def get_store(store_id):
    """
    Args:
        store_id: The unique identifier of the store to be retrieved.

    Returns:
        Response object with the store's extended details in JSON format and an HTTP status code 200 on success.
        Returns an error message in JSON format with an HTTP status code 404 if the store is not found.
    """
    store = StoreModel.get_by_id(store_id)
    if store is None:
        return jsonify({"message": 'Invalid Store Id'}), 404
    store_dict = store.to_dict_extended()
    return jsonify(store_dict), 200


@bp.route("/stores/<int:store_id>", methods=["PUT"])
@login_required
@admin_required
def update_store(store_id: int):
    """
    Args:
        store_id: The unique identifier of the store to be updated.

    Raises:
        StoreNotFoundError: If the store with the given ID does not exist.

    Returns:
        Response object with the store's extended details in JSON format and an HTTP status code 200 on success.
        Returns an error message in JSON format with an HTTP status code 404 if the store is not found.
    """
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400

    try:
        store = StoreModel.update_store(store_id, **data)
        return jsonify(store.to_dict_extended()), 200
    except StoreNotFoundError as e:
        return jsonify({"message": str(e)}), 404

@bp.route("/items", methods=["POST"])
@login_required
@admin_required
def create_item():

    """
    Creates a new item with the provided data.

    Request Body:
        JSON object containing item attributes. 'name' and 'price' are required.

    Returns:
        Response object with the item's key details in JSON format and an HTTP status code 201 on success.
        Returns an error message in JSON format with an HTTP status code 400 for invalid input.

    Example:
        Request:
            POST /items
            {
                "name": "New Item",
                "price": 10.99
            }
        Response:
            201 Created
            {
                "model": "ItemModel",
                "key_id": 12345
            }
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": 'Invalid JSON'}), 400

    try:
        item = ItemModel(**data)
        key = item.put()
        return jsonify({"model": key.kind(), "key_id": key.id()}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 400


@bp.route("/items", methods=['GET'])
@login_required
def get_items():
    """
    Retrieves a list of items based on the provided query parameters.

    Query Parameters:
        page_size: Number of items per page (default: 2).
        cursor: Cursor for pagination (default: None).
        reverse: Boolean indicating whether to reverse the order of results (default: False).
        store_id: ID of the store to filter items by (default: None).

    Returns:
        Response object with a list of items in JSON format and an HTTP status code 200 on success.
        Returns an error message in JSON format with an HTTP status code 404 if the store is not found.
    """
    page_size = request.args.get("page_size", default=2, type=int)
    cursor_str = request.args.get("cursor")
    reverse = request.args.get("reverse", default="false").lower() == "true"
    store_id = request.args.get("store_id")

    cursor = ndb.Cursor(urlsafe=cursor_str) if cursor_str else None
    results = []
    query = ItemModel.query()

    if store_id:
        store_key = ndb.Key(StoreModel, int(store_id))
        query = query.filter(ItemModel.store == store_key)

    order = -ItemModel.created_at if reverse else ItemModel.created_at
    query = query.order(order)

    items, next_cursor, more = query.fetch_page(page_size, start_cursor=cursor)

    for item in items:
        item_dict = item.to_dict_extended()
        item_dict["id"] = item.key.id()
        results.append(item_dict)

    response = {
        "items": results,
        "pagination": {
            "next_cursor": next_cursor.urlsafe().decode("utf-8") if more and next_cursor else None,
            "has_more": more,
            "page_size": page_size,
        }
    }
    return jsonify(response), 200

@bp.route("/items/<int:item_id>", methods=['GET'])
@login_required
def get_item(item_id: int):
    """
    Args:
        item_id: The unique identifier of the item to be retrieved.

    Returns:
        Response object with the item's extended details in JSON format and an HTTP status code 200 on success.
        Returns an error message in JSON format with an HTTP status code 404 if the item is not found.
    """
    item = ndb.Key(ItemModel, item_id).get()
    if item is None:
        return jsonify({"message": 'Invalid item Id'}), 404

    item_dict = item.to_dict_extended()
    return jsonify(item_dict), 200

@bp.route("/items/<int:item_id>/buy", methods=["POST"])
@login_required
def buy_item(item_id: int):
    """
    Args:
        item_id: The unique identifier of the item to be purchased.

    Raises:
        ItemNotFoundError: If the item with the given ID does not exist.
        ItemSoldOutError: If the item is sold out and cannot be purchased.

    Returns:
        Response object with the item's extended details in JSON format and an HTTP status code 200 on success.
        Returns an error message in JSON format with an HTTP status code 404 if the item is not found,
        or 400 if the item is sold out.
    """
    try:
        item = ItemModel.consume_item(item_id)
        task_payload = {
            "user_id": current_user.get_id(),
            "item_id": item_id,
            "store_id": item.store.id(),
            "timestamp": datetime.datetime.now().isoformat()
        }
        enqueue_task(target='/tasks/log_item_consumed', queue_name='log-item-consumed', payload=task_payload)

        return jsonify(item.to_dict_extended()), 200
    except ItemNotFoundError as e:
        return jsonify({"message": str(e)}), 404
    except ItemSoldOutError as e:
        return jsonify({"message": str(e)}), 400

@bp.route("/items/<int:item_id>", methods=["PUT"])
@login_required
@admin_required
def update_item(item_id: int):
    """
    Args:
        item_id: The unique identifier of the item to be updated.
    """
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    try:
        item = ItemModel.update_item(item_id, **data)
        return jsonify(item.to_dict_extended()), 200
    except ItemNotFoundError as e:
        return jsonify({"message": str(e)}), 404
    except InvalidItemQuantity as e:
        return jsonify({"message": str(e)}), 400
    except InvalidItemPrice as e:
        return jsonify({"message": str(e)}), 400

@bp.route("/events", methods=["GET"])
@login_required
def get_events():
    # TODO CHANGE THIS TO ANALYTICS
    events = get_cached_events()
    return jsonify(events)
