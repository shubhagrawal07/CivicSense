from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


# usual session-per-request dependency, same shape as the one in the fastapi sql docs
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
