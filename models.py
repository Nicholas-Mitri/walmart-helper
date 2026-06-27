from database import Base
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Float,
    DateTime,
    text,
)
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime)

    # Relationships
    picks = relationship("Pick", back_populates="user", cascade="all, delete")
    activity_logs = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), unique=True, nullable=False)
    upc = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    brand = Column(String(100))
    description = Column(String)
    food_condition = Column(String(50))
    image_url = Column(String(500))
    url = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False, default="Other")
    subcategory = Column(String(255), nullable=False, default="Other")
    is_discontinued = Column(Boolean, nullable=False, default=False)
    is_stocked = Column(Boolean, nullable=False, default=True)


class Pick(Base):
    __tablename__ = "picks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, default=1
    )
    quantity = Column(Integer, nullable=False, default=1)

    product = relationship("Product")
    user = relationship("User")


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, default=1
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    action = Column(String(25), nullable=False)  # Maps ENUM values as VARCHAR

    cases_qty = Column(Integer, nullable=True)
    units_qty = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    logged_at = Column(DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP"))

    user = relationship("User")
    product = relationship("Product")
