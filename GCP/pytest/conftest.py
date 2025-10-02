import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from google.appengine.ext import ndb, testbed
from app import create_app

@pytest.fixture
def ndb_stub():
    tb = testbed.Testbed()
    tb.activate()
    tb.init_datastore_v3_stub()
    tb.init_memcache_stub()
    ndb.get_context().clear_cache()
    yield tb
    tb.deactivate()


@pytest.fixture
def client(ndb_stub):
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
