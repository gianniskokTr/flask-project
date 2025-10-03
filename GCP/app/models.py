import logging

from flask import jsonify
from google.appengine.ext import ndb
from typing import Optional
from app.exceptions import (
    ItemNotFoundError,
    ItemSoldOutError,
    OutOfStorageError,
    StoreNotFoundError,
    InvalidItemQuantity
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

class SerializationMixin:
    def to_dict_extended(self, key_attribute: Optional[str]):
        data = self.to_dict()
        if key_attribute:
            key_obj = getattr(self, key_attribute, None)
            if isinstance(key_obj, ndb.Key):
                data[key_attribute] = key_obj.id()
        return data

class StoreModel(ndb.Model, SerializationMixin):
    name = ndb.StringProperty(required=True)
    description = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    @ndb.transactional()
    def update_description(cls, store_id: int, description: Optional[str]):
        store = ndb.Key(cls, store_id).get()
        if store is None:
            raise StoreNotFoundError("Invalid store id")
        store.description = description
        store.put()
        return store

class ItemModel(ndb.Model, SerializationMixin):
    name = ndb.StringProperty(required=True)
    price = ndb.FloatProperty(required=True)
    description = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    store = ndb.KeyProperty(kind=StoreModel, required=True)
    quantity = ndb.IntegerProperty(required=True)

    @classmethod
    @ndb.transactional()
    def consume_item_tx(cls, item_id: int):
        item = ndb.Key(cls, item_id).get()
        if item is None:
            raise ItemNotFoundError("Invalid item id")
        if item.quantity is None or item.quantity < 1:
            raise ItemSoldOutError("Item sold out")
        item.quantity -= 1
        item.put()
        return item

    @classmethod
    @ndb.transactional()
    def update_description(cls, item_id: int, description: Optional[str]):
        item = ndb.Key(cls, item_id).get()
        if item is None:
            raise ItemNotFoundError('Invalid item id')
        item.description = description
        item.put()
        return item

    @classmethod
    @ndb.transactional()
    def update_quantity(cls, item_id: int, quantity: int):
        item = ndb.Key(cls, item_id).get()
        if item is None:
            raise ItemNotFoundError('Invalid item id')
        if quantity < 0:
            raise InvalidItemQuantity('Quality must be at least 0')
        item.quantity = quantity
        item.put()
        return item



