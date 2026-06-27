from fastapi import APIRouter, HTTPException, Path, Query
import models
from database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Annotated
from fastapi import Depends
from starlette import status
from pydantic import BaseModel, Field

# Create an instance of the FastAPI application
router = APIRouter(prefix="/picks_list", tags=["picks"])


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
    stmt = select(models.Pick)
    result = db.execute(stmt)
    picks = result.scalars().all()
    return picks


# Pydantic model for request validation when creating a new pick.
class PickRequest(BaseModel):
    product_id: int = Field(gt=0)  # id of product to be picked
    user_id: int = Field(default=1)  # id of user assigned to pick task
    quantity: int = Field(
        gt=0, lt=11, description="Number of cases to pick, must be between 1 and 10"
    )


# Route for creating a new pick item.
@router.post("/mark-for-pick", status_code=status.HTTP_201_CREATED)
async def create_pick(db: db_dependency, pick_request: PickRequest):
    pick_model = models.Pick(**pick_request.model_dump())
    db.add(pick_model)
    db.commit()
    db.refresh(pick_model)
    return {"id": pick_model.id, "product_id": pick_model.product_id, "quantity": pick_model.quantity}


@router.delete("/unmark_for_pick/{pick_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, pick_id: int = Path(gt=0)):
    stmt = select(models.Pick).where(models.Pick.id == pick_id)
    result = db.execute(stmt)
    pick = result.scalar_one_or_none()
    if not pick:
        raise HTTPException(status_code=404, detail="Requested pick not found")
    db.delete(pick)
    db.commit()


# Route for updating the quantity of cases for a specific pick
@router.put("/update_quantity/{pick_id}", status_code=status.HTTP_200_OK)
async def update_pick_quantity(
    db: db_dependency,
    pick_id: int = Path(gt=0),
    quantity: int = Query(
        gt=0, lt=11, description="New number of cases to pick, must be between 1 and 10"
    ),
):
    stmt = select(models.Pick).where(models.Pick.id == pick_id)
    result = db.execute(stmt)
    pick = result.scalar_one_or_none()
    if not pick:
        raise HTTPException(status_code=404, detail="Requested pick not found")
    pick.quantity = quantity
    db.commit()
    db.refresh(pick)
    return {
        "id": pick.id,
        "product_id": pick.product_id,
        "user_id": pick.user_id,
        "quantity": pick.quantity,
    }
