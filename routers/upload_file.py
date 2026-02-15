import hashlib
import os

import aiofiles
from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.DatabaseManager import get_db, db_manager

load_dotenv()
PATH = os.getenv("DATA_PATH")

router = APIRouter(
    prefix="/file",
    tags=["File"]
)


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
