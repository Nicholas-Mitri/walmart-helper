from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DB_PASSWORD = os.getenv("DB_PASSWORD")


# Select which DB to use; currently set to use postgres
SQLALCHEMY_DATABASE_URL = os.getenv("MYSQL_DATABASE_URL")
SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("{}", DB_PASSWORD)

# Create the SQLAlchemy engine object.
# For SQLite, use special connect_args for multithreading.
engine_sql = (
    create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else create_engine(SQLALCHEMY_DATABASE_URL)
)

# Factory for creating session objects to interact with the DB.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_sql)
