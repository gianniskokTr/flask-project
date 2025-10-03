from flask import jsonify, request
from google.appengine.ext import ndb

from app.models import StoreModel, ItemModel, logger
from app.main import bp
from app.exceptions import (
    ItemNotFoundError,
    ItemSoldOutError,
    OutOfStorageError,
    StoreNotFoundError,
    InvalidItemQuantity
)


@bp.route("/store", methods=["POST"])
def create_store():
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
    store_key = ndb.Key(StoreModel, store_id)
    store = store_key.get()
    if store is None:
        return jsonify({"message": 'Invalid Store Id'}), 404

    page_size = request.args.get("page_size", default=2, type=int)
    cursor_str = request.args.get("cursor")
    reverse = request.args.get("reverse", default="false").lower() == "true"

    cursor = ndb.Cursor(urlsafe=cursor_str) if cursor_str else None

    query = ItemModel.query(ItemModel.store == store_key)

    if reverse:
        query = query.order(-ItemModel.created_at)
    else:
        query = query.order(ItemModel.created_at)
    items, next_cursor, more = query.fetch_page(page_size, start_cursor=cursor)

    results = []
    for item in items:
        item_dict = item.to_dict()
        item_dict["id"] = item.key.id()
        item_dict["store"] = item.store.id()
        results.append(item_dict)
    store_dict = store.to_dict()
    store_dict["items"] = results
    store_dict['pagination'] = {
        "next_cursor": next_cursor.urlsafe().decode("utf-8") if more and next_cursor else None,
        "prev_cursor": cursor.urlsafe().decode("utf-8") if cursor else None,
        "has_more": more,
    }
    return jsonify(store_dict)

@bp.route("/store/<int:store_id>/description", methods=["PATCH"])
def update_store_description(store_id):
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    description = data.get("description")
    try:
        store = StoreModel.update_description(store_id, description)
        return jsonify(store.to_dict_extended(key_attribute=None)), 200
    except StoreNotFoundError as e:
        return jsonify({"message": str(e)}), 404

@bp.route("/item", methods=["POST"])
def create_item():
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

@bp.route("/item/<int:item_id>", methods=['GET'])
def get_item(item_id):
    item = ndb.Key(ItemModel, item_id).get()
    if item is None:
        return jsonify({"message": 'Invalid item Id'}), 404

    item_dict = item.to_dict()
    item_dict["store"] = item.store.id()
    return jsonify(item_dict)

@bp.route("/item/<int:item_id>/buy", methods=["POST"])
def buy_single_item(item_id):
    try:
        item = ItemModel.consume_item_tx(item_id)
        return jsonify(item.to_dict_extended(key_attribute='store')), 200
    except ItemNotFoundError as e:
        return jsonify({"message": str(e)}), 404
    except ItemSoldOutError as e:
        return jsonify({"message": str(e)}), 400

@bp.route("/item/<int:item_id>/quantity", methods=["PATCH"])
def update_item_quantity(item_id):
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    quantity = data.get("quantity")
    try:
        item = ItemModel.update_quantity(item_id, quantity)
        return jsonify(item.to_dict_extended(key_attribute='store')), 200
    except ItemNotFoundError as e:
        return jsonify({"message": str(e)}), 404
    except InvalidItemQuantity as e:
        return jsonify({"message": str(e)}), 404

@bp.route("/item/<int:item_id>/description", methods=["PATCH"])
def update_item_description(item_id):
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    description = data.get("description")
    try:
        item = ItemModel.update_description(item_id, description)
        return jsonify(item.to_dict_extended(key_attribute='store')), 200
    except ItemNotFoundError as e:
        return jsonify({"message": str(e)}), 404
