from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status
from datetime import datetime as dt
import item_scraper

app = FastAPI()


class TaskRequest(BaseModel):
    item_url: str
    assigned_to: str
    quantity: int
    action: str


@app.post("/log_task/", status_code=status.HTTP_201_CREATED)
async def log_task(request: TaskRequest):
    try:
        response_data = {
            "status": "success",
            "message": "Task added.",
            "task_timestamp": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": request.model_dump(),
        }
        item_url = request.model_dump()["item_url"]
        item_info = item_scraper.test(item_url)
        return JSONResponse(status_code=200, content=response_data)
    except Exception as e:
        error_response = {
            "status": "error",
            "message": f"An error occurred while processing the task: {str(e)}",
        }
        return JSONResponse(status_code=500, content=error_response)
