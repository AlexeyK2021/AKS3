import hashlib
import os

import aiofiles
from dotenv import load_dotenv
from fastapi import APIRouter, Path, UploadFile, File, Request
from typing import Annotated

from starlette.responses import FileResponse

load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")
router = APIRouter(
    prefix="/file",
    tags=["File"]
)


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@router.get("/{chunk_id}")
async def get_file(chunk_id: Annotated[str, Path(title="ID of chunk")]):
    files = os.listdir(DATA_PATH)
    if chunk_id in files:
        return FileResponse(f"{DATA_PATH}/{chunk_id}", status_code=200)
    else:
        return 404


@router.post("/{chunk_id}")
async def upload_file(chunk_id: str, request: Request):
    content = await request.body()

    file_path = os.path.join(DATA_PATH, chunk_id)
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(content)

    md5sum = md5(f"{DATA_PATH}/{chunk_id}")
    return {"chunk_hash": md5sum}


@router.delete("/{chunk_id}")
async def delete_file(chunk_id: Annotated[str, Path(title="ID of chunk")]):
    files = os.listdir(f"{DATA_PATH}")

    if chunk_id in files:
        os.remove(f"{DATA_PATH}/{chunk_id}")
        return 200
    else:
        return 404
