from fastapi import FastAPI
from models import Base
from database import engine_sql
from routers import activity_log, pick_list, product_catalog

app = FastAPI()

Base.metadata.create_all(bind=engine_sql)


@app.get("/healthy")
async def root():
    return {"status": "healthy"}


app.include_router(product_catalog.router)
app.include_router(pick_list.router)
app.include_router(activity_log.router)
