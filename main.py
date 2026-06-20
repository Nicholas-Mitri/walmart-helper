from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status
from datetime import datetime as dt

app = FastAPI()


class RestockRequest(BaseModel):
    item_url: str
    assigned_to: str
    quantity: int


@app.post("/to_restock/", status_code=status.HTTP_201_CREATED)
async def restock(request: RestockRequest):
    try:
        # Here you can add your logic to process the restock request.
        # For demonstration, we'll just return the received data.
        response_data = {
            "status": "success",
            "message": "Restock task added.",
            "task_timestamp": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": request.model_dump(),
        }
        return JSONResponse(status_code=200, content=response_data)
    except Exception as e:
        error_response = {
            "status": "error",
            "message": f"An error occurred while processing the restock task: {str(e)}",
        }
        return JSONResponse(status_code=500, content=error_response)
