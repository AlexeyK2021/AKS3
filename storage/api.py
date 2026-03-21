import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
import os
import psutil

from routes import file

load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")

app = FastAPI(root_path="/api")
app.include_router(file.router)


def bytes_to_gb(bytes):
    return round(bytes / (1024 ** 3), 2)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@app.get("/status")
async def status():
    disk = psutil.disk_usage(DATA_PATH)
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage_gb": bytes_to_gb(disk.used),
        "disk_total_gb": bytes_to_gb(disk.total),
    }


if __name__ == "__main__":
    if DATA_PATH not in os.listdir():
        os.mkdir(DATA_PATH)
    try:
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT")), log_level="info")
    except KeyboardInterrupt:
        print("Shutting down API server")
