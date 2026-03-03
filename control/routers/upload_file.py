import hashlib
import os

import aiofiles
import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from control.database.DatabaseManager import get_db, db_manager

load_dotenv()
PATH = os.getenv("DATA_PATH")

router = APIRouter(
    prefix="/file",
    tags=["File"]
)


async def find_free_nodes(db: AsyncSession = Depends(get_db)) -> list:
    storages = await db_manager.get_storages()
    online_storages = []
    async with httpx.AsyncClient() as client:
        for node in storages:
            address = f"{node.ip}:{node.port}"
            response = await client.get(f"http://{address}/api/status")
            if response.status_code == 200:
                online_storages.append({address: response.json()})
    return online_storages


@router.get("/upload/testdb")
async def testdb():
    storages = await find_free_nodes()
    return {"storages": storages}


@router.put("/upload")
async def upload_file(
        file: UploadFile = File(),
        db: AsyncSession = Depends(get_db)
):
    sha256_hash = hashlib.sha256()
    temp_path = f"{PATH}/temp_{file.filename}"

    async with aiofiles.open(temp_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):
            sha256_hash.update(content)

            await out_file.write(content)

    file_hash = sha256_hash.hexdigest()
    final_path = f"{PATH}/{file_hash}"

    if os.path.exists(final_path):
        os.remove(temp_path)
    else:
        os.rename(temp_path, final_path)

    await db_manager.save_file_info(file_hash, file.filename, final_path, file.size)

    return {"status": "success", "hash": file_hash, "filename": file.filename}
