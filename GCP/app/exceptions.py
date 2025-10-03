class ItemNotFoundError(Exception):
    pass

class ItemSoldOutError(Exception):
    pass

class InvalidItemQuantity(Exception):
    pass

class OutOfStorageError(Exception):
    pass

class StoreNotFoundError(Exception):
    pass
