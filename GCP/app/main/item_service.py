
from google.appengine.ext import ndb

@ndb.transactional()
def consume_item_tx(item_id):
    item = ndb.Key('ItemModel', item_id).get()

    if item.quantity is None or item.quantity < 1:
        raise ValueError("Item sold out")

    item.quantity -= 1
    item.put()
    return item
