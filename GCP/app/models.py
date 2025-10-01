from google.appengine.ext import ndb

class StoreModel(ndb.Model):
    name = ndb.StringProperty(required=True)
    description = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)

class ItemModel(ndb.Model):
    name = ndb.StringProperty(required=True)
    price = ndb.FloatProperty(required=True)
    description = ndb.TextProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    store = ndb.KeyProperty(kind="StoreModel", required=True)
    quantity = ndb.IntegerProperty(required=True)
