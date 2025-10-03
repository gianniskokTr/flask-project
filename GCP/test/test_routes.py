from google.appengine.ext import ndb

from app.models import StoreModel, ItemModel

def test_create_store_endpoint(client):
    response = client.post("/store", json={"name": "Init Store"})
    data = response.get_json()
    assert response.status_code == 201
    assert "key_id" in data
    assert "model" in data
