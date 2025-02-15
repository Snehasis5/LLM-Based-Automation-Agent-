import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional

# Assuming 'run_task' is the function from 'app/agent.py' that will process the task.
from agent import run_task  

app = FastAPI()

# Define a Pydantic model for request validation
class RunTaskRequest(BaseModel):
    task: str
    # Optionally, other task details like task_id, etc.

@app.post("/run")
async def run_endpoint(task: str):  # Using query parameter for simplicity
    """
    Endpoint to run a task.
    """
    try:
        # Assuming run_task is an async function that processes the task
        await run_task(task)
        return {"message": "Task executed successfully"}
    except ValueError as e:
        # Handle known errors with a 400 Bad Request status
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors with a 500 Internal Server Error status
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/read")
async def read_endpoint(path: str):
    """
    Returns the content of the specified file.
    """
    try:
        # Security: Ensure the file path is within the allowed directory
        if not path.startswith("/data/"):
            raise HTTPException(status_code=400, detail="Path must be within /data/")

        # Check if file exists before reading
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")

        # Open the file and read its content
        with open(path, "r") as f:
            content = f.read()
        return PlainTextResponse(content, media_type="text/plain")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
