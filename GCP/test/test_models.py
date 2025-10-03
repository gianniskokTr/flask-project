from google.appengine.ext import ndb

from app.models import StoreModel, ItemModel

def test_create_store(ndb_stub):
    store = StoreModel(name="Init Store", description="Init Desc")
    key = store.put()
    retrieved = key.get()
    assert retrieved.name == "Init Store"




