from flask import jsonify, request
from google.appengine.ext import ndb
from flask_login import login_required, current_user

from app.models import StoreModel, ItemModel, logger
from app.core import bp
from app.exceptions import (
    ItemNotFoundError,
    ItemSoldOutError,
    OutOfStorageError,
    StoreNotFoundError,
    InvalidItemQuantity
)
from app.decorators import admin_required

from app.services.bigquery_service import log_item_consumed
from app.services.cache_service import get_cached_events, refresh_cache

@bp.route("/store", methods=["POST"])
@login_required
@admin_required
def create_store():
    """
    Args:
        name: The name of the store to be created.
        description: The description of the store to be created.

    Returns:
        Response object with the store's extended details in JSON format and an HTTP status code 201 on success.
        Returns an error message in JSON format with an HTTP status code 404 if the store is not found.
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": 'Invalid JSON'}), 400

    name = data.get("name")
    description = data.get("description")

    if not name:
        return jsonify({"message": "Store name is required"}), 400

    store = StoreModel(name=name, description=description)
    try:
        key = store.put()
        return jsonify({"model": key.kind(), "key_id": key.id()}), 201
    except:
        return jsonify({"message": 'Error occurred while creating store'}), 500

@bp.route("/store/<int:store_id>", methods=['GET'])
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

    try:
        store_dict = store.to_dict_extended()
        return jsonify(store_dict), 200
    except StoreNotFoundError as e:
        return jsonify({"message": str(e)}), 404

@bp.route("/store/<int:store_id>", methods=["PATCH"])
@login_required
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
    description = data.get("description")
    try:
        store = StoreModel.update_description(store_id, description)
        return jsonify(store.to_dict_extended()), 200
    except StoreNotFoundError as e:
        return jsonify({"message": str(e)}), 404

@bp.route("/item", methods=["POST"])
@login_required
@admin_required
def create_item():
    """
    Args:
        name: The name of the item to be created.
        description: The description of the item to be created.
        price: The price of the item to be created.
        store_id: The unique identifier of the store where the item will be created.
        quantity: The quantity of the item to be created.

    Returns:
        Response object with the item's extended details in JSON format and an HTTP status code 201 on success.
        Returns an error message in JSON format with an HTTP status code 404 if the store is not found.
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": 'Invalid JSON'}), 400

    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    store_id = data.get("store_id")
    quantity = data.get("quantity")

    if not name:
        return jsonify({"message": "Item name is required"}), 400
    if not price:
        return jsonify({"message": "Item price is required"}), 400
    if not store_id:
        return jsonify({"message": "A store_id is required"}), 400
    if not quantity:
        quantity = 0
    store_key = ndb.Key(StoreModel, store_id)
    if store_key.get() is None:
        return jsonify({"message": "Invalid store_id"}), 404

    try:
        item = ItemModel(
            name=name,
            description=description,
            price=price,
            store=store_key,
            quantity=quantity
        )
        key = item.put()
        return jsonify({"model": key.kind(), "key_id": key.id()}), 201
    except:
        return jsonify({"message": 'Error occurred while creating item'}), 500

@bp.route("/item", methods=['GET'])
def get_items():
    page_size = request.args.get("page_size", default=2, type=int)
    cursor_str = request.args.get("cursor")
    reverse = request.args.get("reverse", default="false").lower() == "true"
    store_id = request.args.get("store_id")

    cursor = ndb.Cursor(urlsafe=cursor_str) if cursor_str else None
    results = []

    if store_id is None:
        query = ItemModel.query()

        if reverse:
            query = query.order(-ItemModel.created_at)
        else:
            query = query.order(ItemModel.created_at)

        items, next_cursor, more = query.fetch_page(page_size, start_cursor=cursor)

    else:
        try:
            items, next_cursor, more = ItemModel.get_by_store(int(store_id), page_size, cursor, reverse)
        except StoreNotFoundError as e:
            return jsonify({"message": str(e)}), 404

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


@bp.route("/item/<int:item_id>", methods=['GET'])
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

    item_dict = item.to_dict()
    item_dict["store"] = item.store.id()
    return jsonify(item_dict)

@bp.route("/item/<int:item_id>/buy", methods=["POST"])
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
        item = ItemModel.consume_item_tx(item_id)
        # TODO: add task queue to stream event to BigQuery with retry
        log_item_consumed(
            user_id=current_user.get_id(),
            item_id=item.key.id(),
            store_id=item.store.id()
        )
        return jsonify(item.to_dict_extended()), 200
    except ItemNotFoundError as e:
        return jsonify({"message": str(e)}), 404
    except ItemSoldOutError as e:
        return jsonify({"message": str(e)}), 400

@bp.route("/item/<int:item_id>", methods=["PATCH"])
@login_required
def update_item(item_id: int):
    """
    Args:
        item_id: The unique identifier of the item to be updated.
    """
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    quantity = data.get("quantity")
    description = data.get("description")
    try:
        item = ItemModel.update_item(item_id, description=description, quantity=quantity)
        return jsonify(item.to_dict_extended()), 200
    except ItemNotFoundError as e:
        return jsonify({"message": str(e)}), 404
    except InvalidItemQuantity as e:
        return jsonify({"message": str(e)}), 404

@bp.route("/events", methods=["GET"])
def get_events():
    events = get_cached_events()
    return jsonify(events)

# Endpoint for cron
@bp.route("/tasks/update_cache", methods=["GET"])
def update_cache_task():
    events = refresh_cache()
    return jsonify({"status": "cache updated", "count": len(events)})
