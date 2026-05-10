import pytest
from app import create_app, db


@pytest.fixture
def app_with_db(tmp_path, monkeypatch):
    # use a temporary sqlite file
    config = type('C', (), {})()
    config.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(tmp_path / 'test.db')
    config.SECRET_KEY = 'test'

    app = create_app(config)
    app.testing = True

    yield app


def test_index(app_with_db):
    client = app_with_db.test_client()
    res = client.get('/')
    assert res.status_code == 200
    assert b'Dashboard' in res.data
