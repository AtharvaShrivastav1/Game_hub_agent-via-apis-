import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.base import Base

logger = logging.getLogger(__name__)

def ensure_database_exists():
    """Ensure MySQL database exists before binding session."""
    if settings.sync_database_url.startswith("sqlite"):
        return

    try:
        root_engine = create_engine(settings.root_mysql_url, isolation_level="AUTOCOMMIT")
        with root_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
        root_engine.dispose()
        logger.info(f"Database `{settings.DB_NAME}` verified/created.")
    except Exception as e:
        logger.warning(f"Could not automatically create MySQL database via root connection: {e}. Attempting direct connection...")

# Ensure DB exists first if using MySQL
ensure_database_exists()

# Engine creation
try:
    if settings.sync_database_url.startswith("sqlite"):
        engine = create_engine(
            settings.sync_database_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
    else:
        engine = create_engine(
            settings.sync_database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
except Exception as e:
    logger.error(f"Failed to initialize database engine: {e}")
    # Fallback to local SQLite if MySQL failed unexpectedly
    fallback_url = "sqlite:///./gamehub.db"
    logger.warning(f"Falling back to {fallback_url}")
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_tables():
    """Create all tables defined in Base metadata."""
    Base.metadata.create_all(bind=engine)
