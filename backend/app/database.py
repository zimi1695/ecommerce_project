from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    "mysql+pymysql://ecommerce:ecommerce_2026"
    "@127.0.0.1:3307/ecommerce"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()