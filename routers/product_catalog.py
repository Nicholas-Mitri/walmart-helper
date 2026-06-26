from fastapi import APIRouter, HTTPException, Path
import models
from database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from typing import Annotated
from fastapi import Depends
from starlette import status
from pydantic import BaseModel, Field

# Create an instance of the FastAPI application
router = APIRouter(prefix="/products", tags=["products"])


# Dependency for getting a database session.
# It opens a session for each request and closes it when done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Annotated type for dependency injection in route functions.
db_dependency = Annotated[Session, Depends(get_db)]


# Route for retrieving all todos from the database.
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    stmt = select(models.Product)
    result = db.execute(stmt)
    todos = result.scalars().all()
    return todos


@router.get("/search", status_code=status.HTTP_200_OK)
async def filter_products(
    db: db_dependency,
    search_value: str = None,
    brand: str = None,
    category: str = None,
    subcategory: str = None,
    name: str = None,
    is_discontinued: bool = None,
    is_stocked: bool = None,
):
    stmt = select(models.Product)
    # Build filters dynamically
    filters = []
    if search_value is not None:
        filters.append(
            or_(
                models.Product.name.ilike(f"%{search_value}%"),
                models.Product.brand.ilike(f"%{search_value}%"),
            )
        )
    if brand is not None:
        filters.append(models.Product.brand.ilike(f"%{brand}%"))
    if category is not None:
        filters.append(models.Product.category == category)
    if subcategory is not None:
        filters.append(models.Product.subcategory == subcategory)
    if name is not None:
        filters.append(models.Product.name.ilike(f"%{name}%"))
    if is_discontinued is not None:
        filters.append(models.Product.is_discontinued == False)
    if is_stocked is not None:
        filters.append(models.Product.is_stocked == True)
    if filters:
        stmt = stmt.where(*filters)
    result = db.execute(stmt)
    products = result.scalars().all()
    return products
