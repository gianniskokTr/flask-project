from flask import jsonify, request
from google.appengine.ext import ndb

from app.models import StoreModel, ItemModel
from app.main import bp
from app.main.item_service import consume_item_tx

@bp.route("/store/<int:store_id>", methods=['GET'])
def get_store(store_id):
    store_key = ndb.Key('StoreModel', store_id)
    store = store_key.get()
    if store is None:
        return {"message": 'Invalid Store Id'}, 404
    items = ItemModel.query(ItemModel.store == store_key).fetch()
    results = []
    for item in items:
        item_dict = item.to_dict()
        item_dict["id"] = item.key.id()
        item_dict["store"] = item.store.id()
        results.append(item_dict)
    store_dict = store.to_dict()
    store_dict["items"] = results
    return jsonify(store_dict)

@bp.route("/store", methods=["POST"])
def create_store():
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400

    name = data.get("name")
    description = data.get("description")

    if not name:
        return {"message": "Store name is required"}, 400

    store = StoreModel(name=name, description=description)
    try:
        key = store.put()
        return {"model": key.kind(), "key_id": key.id()}, 201
    except:
        return {"message": 'Error occurred while creating store'}, 500

@bp.route("/update_store_description", methods=["POST"])
def update_store_description():
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    store_id = data.get("store_id")
    description = data.get("description")

    if not store_id:
        return {"message": 'store_id is required '}, 400

    store = ndb.Key('StoreModel', store_id).get()
    if store is None:
        return {"message": 'Invalid store_id'}, 404

    store.description = description
    store.put()
    store_dict = store.to_dict()
    return jsonify(store_dict)

@bp.route("/item/<int:item_id>", methods=['GET'])
def get_item(item_id):
    item = ndb.Key('ItemModel', item_id).get()
    if item is None:
        return {"message": 'Invalid Item Id'}, 404

    item_dict = item.to_dict()
    item_dict["store"] = item.store.id()
    return jsonify(item_dict)

@bp.route("/item", methods=["POST"])
def create_item():
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400

    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    store_id = data.get("store_id")
    quantity = data.get("quantity")

    if not name:
        return {"message": "Item name is required"}, 400
    if not price:
        return {"message": "Item price is required"}, 400
    if not store_id:
        return {"message": "A store_id is required"}, 400
    if not quantity:
        quantity = 0
    store_key = ndb.Key('StoreModel', store_id)
    if store_key.get() is None:
        return {"message": "Invalid store_id"}, 404

    try:
        item = ItemModel(
            name=name,
            description=description,
            price=price,
            store=store_key,
            quantity=quantity
        )
        key = item.put()
        return {"model": key.kind(), "key_id": key.id()}, 201
    except:
        return {"message": 'Error occurred while creating item'}, 500

@bp.route("/buy_item", methods=["POST"])
def buy_single_item():
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    item_id = data.get("item_id")

    if not item_id:
        return {"message": 'item_id is required '}, 400

    item = ndb.Key('ItemModel', item_id).get()
    if item is None:
        return {"message": 'Invalid item_id'}, 404

    try:
        item = consume_item_tx(item_id)
        item_dict = item.to_dict()
        item_dict["store"] = item.store.id()
        return jsonify(item_dict)
    except ValueError as e:
        return {"message": str(e)}, 400


@bp.route("/update_item_quantity", methods=["POST"])
def update_item_quantity():
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    item_id = data.get("item_id")
    quantity = data.get("quantity")

    if not item_id:
        return {"message": 'item_id is required '}, 400

    if not quantity or quantity <= 0:
        return {"message": 'Invalid quantity'}, 400

    item = ndb.Key('ItemModel', item_id).get()
    if item is None:
        return {"message": 'Invalid item_id'}, 404

    item.quantity = quantity
    item.put()
    item_dict = item.to_dict()
    item_dict["store"] = item.store.id()
    return jsonify(item_dict)

@bp.route("/update_item_description", methods=["POST"])
def update_item_description():
    data = request.get_json()
    if not data:
        return {"message": 'Invalid JSON'}, 400
    item_id = data.get("item_id")
    description = data.get("description")

    if not item_id:
        return {"message": 'item_id is required '}, 400

    item = ndb.Key('ItemModel', item_id).get()
    if item is None:
        return {"message": 'Invalid item_id'}, 404

    item.description = description
    item.put()
    item_dict = item.to_dict()
    item_dict["store"] = item.store.id()
    return jsonify(item_dict)
