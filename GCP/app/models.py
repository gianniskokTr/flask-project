from flask import jsonify
from google.appengine.ext import ndb

class StoreModel(ndb.Model):
    name = ndb.StringProperty(required=True)
    description = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    @ndb.transactional()
    def update_description(cls, store_id, description):
        store = ndb.Key(cls, store_id).get()
        if store is None:
            return jsonify({"message": 'Invalid store_id'}), 404
        store.description = description
        store.put()
        store_dict = store.to_dict()
        return jsonify(store_dict), 200

class ItemModel(ndb.Model):
    name = ndb.StringProperty(required=True)
    price = ndb.FloatProperty(required=True)
    description = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    store = ndb.KeyProperty(kind=StoreModel, required=True)
    quantity = ndb.IntegerProperty(required=True)

    @classmethod
    @ndb.transactional()
    def consume_item_tx(cls, item_id):
        item = ndb.Key(cls, item_id).get()
        if item is None:
            return jsonify({"message": 'Invalid item_id'}), 404

        if item.quantity is None or item.quantity < 1:
            return jsonify({"message": 'Item sold out'}), 500

        item.quantity -= 1
        item.put()
        item_dict = item.to_dict()
        item_dict["store"] = item.store.id()
        return jsonify(item_dict), 200

    @classmethod
    @ndb.transactional()
    def update_description(cls, item_id, description):
        item = ndb.Key(cls, item_id).get()
        if item is None:
            return jsonify({"message": 'Invalid item_id'}), 404
        item.description = description
        item.put()
        item_dict = item.to_dict()
        item_dict["store"] = item.store.id()
        return jsonify(item_dict), 200

    @classmethod
    @ndb.transactional()
    def update_quantity(cls, item_id, quantity):
        item = ndb.Key(cls, item_id).get()
        if item is None:
            return jsonify({"message": 'Invalid item_id'}), 404
        item.quantity = quantity
        item.put()
        item_dict = item.to_dict()
        item_dict["store"] = item.store.id()
        return jsonify(item_dict), 200



