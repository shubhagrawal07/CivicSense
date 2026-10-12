import pytest
from sqlalchemy.orm import Session

from app.core.db import engine


# rollback-per-test setup from the sqlalchemy docs ("joining a session into an
# external transaction"), so tests never leave rows behind
@pytest.fixture
def db():
    connection = engine.connect()
    outer = connection.begin()
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint", autoflush=False
    )
    yield session
    session.close()
    outer.rollback()
    connection.close()
