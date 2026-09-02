"""
数据库连接管理
使用 SQLAlchemy 2.0 支持 SQLite 和 MySQL
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


_connect_args = {}
if settings.db_type == "sqlite":
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    pool_size=10 if settings.db_type == "mysql" else 1,
    max_overflow=20 if settings.db_type == "mysql" else 0,
    pool_pre_ping=settings.db_type == "mysql",
    pool_recycle=3600 if settings.db_type == "mysql" else -1,
    echo=settings.debug,
    connect_args=_connect_args,
)


@event.listens_for(engine, "connect")
def set_db_encoding(dbapi_conn, connection_record):
    if settings.db_type == "mysql":
        cursor = dbapi_conn.cursor()
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)