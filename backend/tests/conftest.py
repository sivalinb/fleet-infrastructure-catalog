import pytest
from fleet_catalog.fixtures import seed
from fleet_catalog.models import make_database


@pytest.fixture
def factory(tmp_path):
    engine, factory = make_database("sqlite:///" + str(tmp_path / "test.db"))
    with factory.begin() as db:
        seed(db)
    yield factory
    engine.dispose()
