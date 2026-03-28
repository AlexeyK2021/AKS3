import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
import os
import psutil

from routes import chunks
from storage.routes import status

load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")

app = FastAPI(root_path="/api")
app.include_router(chunks.router)
app.include_router(status.router)


if __name__ == "__main__":
    if DATA_PATH not in os.listdir():
        os.mkdir(DATA_PATH)
    try:
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT")), log_level="info")
    except KeyboardInterrupt:
        print("Shutting down API server")
