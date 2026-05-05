import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from controllers.database_controller import get_chunks_of_file, get_storages
from controllers.database_controller import get_db, get_file_in_bucket, get_files_by_bucket
from controllers.models import EntityTypeEnum, ActionTypeEnum
from log import log

router = APIRouter(
    prefix="/file",
    tags=["File"]
)

load_dotenv()
MINIO_BUCKET_NAME=os.getenv("MINIO_BUCKET_NAME")

@router.get("/in/{bucket_id}")
async def get_files_in_bucket(bucket_id: int, db: AsyncSession = Depends(get_db)):
    return await get_files_by_bucket(bucket_id, db)


executor = ThreadPoolExecutor(max_workers=10)

@router.get("/{file_id}")
async def download_file(
        file_id: int,
        session: AsyncSession = Depends(get_db)
):
    file = await get_file_in_bucket(file_id, session)
    if not file:
        await log(
            entity_name=f"{file_id}",
            entity_type=EntityTypeEnum.FILE,
            action=ActionTypeEnum.DOWNLOAD,
            description="Файл не найден",
            success=False,
            session=session
        )
        raise HTTPException(status_code=404, detail="Файл не найден")

    chunks = await get_chunks_of_file(session, file_id)
    if not chunks:
        await log(
            entity_name=f"{file_id}",
            entity_type=EntityTypeEnum.CHUNK,
            action=ActionTypeEnum.DOWNLOAD,
            description="Блоки файла не найдены",
            success=False,
            session=session
        )
        raise HTTPException(status_code=404, detail="Блоки файла не найдены")

    storages_list = await get_storages(session)

    storage_keys_map = {
        (s.ip, s.port): {"access": s.access_key, "secret": s.secret_key}
        for s in storages_list
    }

    chunk_map = {}
    for chunk_uuid, chunk_index, ip, port in chunks:
        if chunk_index not in chunk_map:
            chunk_map[chunk_index] = []

        keys = storage_keys_map.get((ip, port))

        if not keys:
            print(f"ВНИМАНИЕ: Ключи для ноды {ip}:{port} не найдены в БД")
            continue

        chunk_map[chunk_index].append({
            "uuid": chunk_uuid,
            "node_url": f"{ip}:{port}",
            "access_key": keys["access"],
            "secret_key": keys["secret"]
        })

    ordered_indexes = sorted(chunk_map.keys())

    async def file_stream():
        loop = asyncio.get_running_loop()


        for index in ordered_indexes:
            replicas = chunk_map[index]
            chunk_downloaded = False

            for replica in replicas:
                try:
                    client = Minio(
                        replica["node_url"],
                        access_key=replica["access_key"],
                        secret_key=replica["secret_key"],
                        secure=False
                    )

                    def fetch_from_minio():
                        response = client.get_object(MINIO_BUCKET_NAME, replica["uuid"])
                        try:
                            return response.read()
                        finally:
                            response.close()
                            response.release_conn()

                    chunk_data = await loop.run_in_executor(executor, fetch_from_minio)

                    yield chunk_data
                    chunk_downloaded = True
                    break

                except Exception as e:
                    await log(
                        entity_name=f"{replica['uuid']}",
                        entity_type=EntityTypeEnum.CHUNK,
                        action=ActionTypeEnum.DOWNLOAD,
                        description="Ошибка при скачивании чанка",
                        success=False,
                        session=session
                    )
                    print(f"Ошибка при скачивании чанка {replica['uuid']} с {replica['node_url']}: {e}")
                    continue

            if not chunk_downloaded:
                raise HTTPException(
                    status_code=500,
                    detail=f"Не удалось восстановить блок index={index}"
                )

    return StreamingResponse(
        file_stream(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={file.filename}"
        }
    )
