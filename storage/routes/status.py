import os

import psutil
from dotenv import load_dotenv
from fastapi import APIRouter

router = APIRouter(
    prefix="",
    tags=["Status"]
)

load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")


def bytes_to_gb(bytes):
    return round(bytes / (1024 ** 3), 2)


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@router.get("/status")
async def status():
    disk = psutil.disk_usage(DATA_PATH)
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage_gb": bytes_to_gb(disk.used),
        "disk_total_gb": bytes_to_gb(disk.total),
    }
