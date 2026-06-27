from fastapi import APIRouter, HTTPException, Path, Query
import models
from database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date
from typing import Annotated
from fastapi import Depends
from starlette import status
from pydantic import BaseModel, Field
from typing import Literal

# Create an instance of the FastAPI application
router = APIRouter(prefix="/activity_log", tags=["log"])


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
    stmt = select(models.ActivityLog)
    result = db.execute(stmt)
    activities = result.scalars().all()
    return activities


ActivityLogActionType = Literal[
    "throw",
    "cvp",
    "vizpik",
    "restock",
    "clean_daily",
    "clean_pm",
    "temp_check",
    "general_note",
    "product_note",
    "donate",
    "floor_sweep",
    "recovery",
]


# Pydantic model for request validation when creating a new pick.
class ActivityLogRequest(BaseModel):
    user_id: int = Field(default=1, gt=0, description="ID of the user, must be > 0")
    product_id: int | None = Field(
        default=None, gt=0, description="ID of the product, optional"
    )
    action: ActivityLogActionType = Field(..., description="Action performed")
    cases_qty: int | None = Field(
        default=None, gt=0, description="Number of cases involved, if applicable"
    )
    units_qty: int | None = Field(
        default=None, gt=0, description="Number of units involved, if applicable"
    )
    notes: str | None = Field(default=None, description="Optional notes for the log")


# Route for creating a new pick item.
@router.post("/log-activity", status_code=status.HTTP_201_CREATED)
async def create_pick(db: db_dependency, log_request: ActivityLogRequest):
    # Convert the incoming Pydantic model to a SQLAlchemy model.
    log_model = models.ActivityLog(**log_request.model_dump())
    db.add(log_model)
    db.commit()


@router.delete("/delete-activity/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, activity_id: int = Path(gt=0)):
    stmt = select(models.ActivityLog).where(models.ActivityLog.id == activity_id)
    result = db.execute(stmt)
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Requested pick not found")
    db.delete(log)
    db.commit()


@router.get("/feed", status_code=status.HTTP_200_OK)
async def get_feed(db: db_dependency):
    today = date.today()
    stmt = (
        select(models.ActivityLog)
        .where(func.date(models.ActivityLog.logged_at) == today)
        .order_by(models.ActivityLog.logged_at.asc(), models.ActivityLog.id.asc())
        .limit(200)
    )
    result = db.execute(stmt)
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "product_name": log.product.name if log.product else None,
            "cases_qty": log.cases_qty,
            "units_qty": log.units_qty,
            "notes": log.notes,
            "logged_at": log.logged_at.isoformat() if log.logged_at else None,
        }
        for log in logs
    ]
