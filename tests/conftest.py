import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp(prefix='solar-tests-')}/test.db"
os.environ["SECRET_KEY"] = "a-dedicated-test-key-longer-than-32-characters"

import pytest
from fastapi.testclient import TestClient

from backend.db import Base, engine
from backend.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as browser:
        yield browser
