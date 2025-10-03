from google.appengine.ext import ndb
from typing import Optional, Union, List
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import logging

from app import login
from app.exceptions import (
    ItemNotFoundError,
    ItemSoldOutError,
    OutOfStorageError,
    StoreNotFoundError,
    InvalidItemQuantity,
    UserAlreadyExistsError
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

class SerializationMixin:
    def to_dict_extended(self, key_attribute: Optional[str]) -> dict:
        """
            Converts the model to a dictionary, with the option to include a key attribute.

            If key_attribute is provided, and the attribute is an ndb.Key, it will be included in the
            returned dictionary with its id() as the value.

            :param key_attribute: The name of the key attribute to include
            :type key_attribute: Optional[str]
            :return: A dictionary representation of the model
            :rtype: dict
        """
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
    def get_by_id(cls, store_id: int) -> Union['StoreModel', None]:
        store = ndb.Key(cls, store_id).get()
        return store

    @classmethod
    @ndb.transactional()
    def update_description(cls, store_id: int, description: Optional[str]) -> Union['StoreModel', None]:
        """
            Updates the description of a store.

            Args:
                store_id (int): the id of the store to update
                description (Optional[str]): the new description of the store

            Returns:
                Union['StoreModel', None]: the updated store object, or None if the store was not found

            Raises:
                StoreNotFoundError: if the store is not found
        """
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
    def get_by_id(cls, item_id: int) -> Union['ItemModel', None]:
        item = ndb.Key(cls, item_id).get()
        return item

    @classmethod
    def get_by_store(cls, store_id: int, page_size: int = 2, cursor: Optional[str] = None, reverse: bool = False) -> (List['ItemModel'], Optional[str], bool):
        store = StoreModel.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError("Invalid store id")

        store_key = store.key
        query = cls.query(ItemModel.store == store_key)
        if reverse:
            query = query.order(-ItemModel.created_at)
        else:
            query = query.order(ItemModel.created_at)
        items, next_cursor, more = query.fetch_page(page_size, start_cursor=cursor)
        return items, next_cursor, more

    @classmethod
    @ndb.transactional()
    def consume_item_tx(cls, item_id: int) -> Union['ItemModel', None]:
        """
            Consumes an item by decrementing its quantity.

            Args:
                item_id (int): the id of the item to consume

            Returns:
                Union['ItemModel', None]: the updated item object, or None if the item was not found

            Raises:
                ItemNotFoundError: if the item is not found
                ItemSoldOutError: if the item is sold out
        """
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
    def update_description(cls, item_id: int, description: Optional[str]) -> Union['ItemModel', None]:
        """
            Updates the description of an item.

            Args:
                item_id (int): the id of the item to update
                description (Optional[str]): the new description of the item

            Returns:
                Union['ItemModel', None]: the updated item object, or None if the item was not found

            Raises:
                ItemNotFoundError: if the item is not found
        """
        item = ndb.Key(cls, item_id).get()
        if item is None:
            raise ItemNotFoundError('Invalid item id')
        item.description = description
        item.put()
        return item

    @classmethod
    @ndb.transactional()
    def update_quantity(cls, item_id: int, quantity: int) -> Union['ItemModel', None]:
        """
            Updates the quantity of an item.

            Args:
                item_id (int): the id of the item to update
                quantity (int): the new quantity of the item

            Returns:
                Union['ItemModel', None]: the updated item object, or None if the item was not found

            Raises:
                ItemNotFoundError: if the item is not found
                InvalidItemQuantity: if the quantity is less than 0
        """
        item = ndb.Key(cls, item_id).get()
        if item is None:
            raise ItemNotFoundError('Invalid item id')
        if quantity < 0:
            raise InvalidItemQuantity('Quality must be at least 0')
        item.quantity = quantity
        item.put()
        return item


class User(UserMixin, ndb.Model, SerializationMixin):
    username = ndb.StringProperty(required=True)
    password_hash = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    is_active = ndb.BooleanProperty(default=True)
    is_admin = ndb.BooleanProperty(default=False)

    def to_dict(self):
        return {
            "id": self.key.id(),
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at,
            "is_active": self.is_active,
            "is_admin": self.is_admin
        }

    def get_id(self):
        return self.key.id()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        return cls.query(User.email == email).get()

    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        return cls.query(User.username == username).get()

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        return ndb.Key(cls, user_id).get()

    @classmethod
    def create_user(cls, username: str, email: str, password: str, is_admin: bool = False) -> Union[ndb.Key, None]:
        if cls.get_by_email(email):
            raise UserAlreadyExistsError("User with this email already exists")
        if cls.get_by_username(username):
            raise UserAlreadyExistsError("User with this username already exists")
        user = cls(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        key = user.put()
        return key

@login.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))