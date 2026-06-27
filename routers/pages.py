from datetime import date
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Product, Pick

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def today() -> str:
    return date.today().isoformat()  # e.g. "2026-06-25"


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.name).all()
    shift_date = today()
    picks = db.query(Pick).all()
    picked_skus = {p.product.sku for p in picks}
    picks_data = [
        {
            "id": p.id,
            "product_id": p.product_id,
            "sku": p.product.sku,
            "name": p.product.name,
            "brand": p.product.brand or "",
            "image_url": p.product.image_url or "",
            "quantity": p.quantity,
            "category": p.product.category,
        }
        for p in picks
    ]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "products": products,
            "picked_skus": picked_skus,
            "shift_date": shift_date,
            "picks_data": picks_data,
        },
    )
