import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from read.controllers.DatabaseController import get_chunks_of_file
from read.controllers.DatabaseController import get_db, get_file_in_bucket, get_files_by_bucket
from read.controllers.models import FileStatusEnum

router = APIRouter(
    prefix="/file",
    tags=["File"]
)


@router.get("/{bucket_id}")
async def get_files_in_bucket(bucket_id: int, db: AsyncSession = Depends(get_db)):
    return await get_files_by_bucket(bucket_id, db)


@router.get("/{file_id}")
async def download_file(
        file_id: int,
        db: AsyncSession = Depends(get_db)
):
    file = await get_file_in_bucket(file_id, db)
    if not file or file.status_id != FileStatusEnum.ACTIVE:
        raise HTTPException(status_code=404, detail="Файл не найден или не готов")

    chunks = await get_chunks_of_file(db, file_id)

    if not chunks:
        raise HTTPException(status_code=404, detail="Блоки файла не найдены")

    chunk_map = {}

    for chunk_id, chunk_index, ip, port in chunks:
        url = f"http://{ip}:{port}/file/{chunk_id}"

        if chunk_index not in chunk_map:
            chunk_map[chunk_index] = []

        chunk_map[chunk_index].append({
            "chunk_id": chunk_id,
            "url": url
        })

    ordered_indexes = sorted(chunk_map.keys())

    async def file_stream():
        async with httpx.AsyncClient(timeout=60.0) as client:

            for index in ordered_indexes:
                replicas = chunk_map[index]
                chunk_downloaded = False

                for replica in replicas:
                    try:
                        response = await client.get(replica["url"])
                        if response.status_code == 200:
                            yield response.content
                            chunk_downloaded = True
                            break

                    except Exception:
                        continue  # пробуем следующую ноду

                if not chunk_downloaded:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Не удалось скачать блок index={index}"
                    )

    return StreamingResponse(
        file_stream(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={file.filename}"
        }
    )

#
# # TODO() Think about adding file, chunk, chunk_storage data into controllers only after its writing
# @router.post("/{bucket_id}")
# async def upload_file(bucket_id: int, file: UploadFile, db: AsyncSession = Depends(get_db)):
#     original_name = file.filename
#
#     target_nodes = await get_most_relevant(await find_online_nodes(db))
#
#     if not target_nodes:
#         raise HTTPException(status_code=503, detail="Нет доступных нод")
#
#     log("FILE_API", f"Начита загрузка файла: {original_name}")
#     session = await db_manager.get_session()
#     new_file = File(filename=original_name, status_id=FileStatusEnum.UPLOADING, bucket_id=bucket_id)
#     try:
#         await add_file_info(new_file, session)
#         result = await process_file_upload(file, original_name, target_nodes, session)
#         new_file.status_id = FileStatusEnum.ACTIVE
#
#         return {
#             "filename": original_name,
#             "bucket_id": bucket_id,
#             "chunks": result['total_chunks'],
#             "nodes": target_nodes,
#             "status": "success"
#         }
#
#     except Exception as e:
#         new_file.status_id = FileStatusEnum.ERROR
#         raise HTTPException(status_code=500, detail=f"Ошибка при сохранении блоков: {str(e)}")
#     finally:
#         await commit_session(session)
#         await db_manager.close_session()
#
#
# @router.delete("/{bucket_id}/{file_id}")
# async def delete_file(bucket_id: int, file_id: int, db: AsyncSession = Depends(get_db)):
#     file = await get_file_in_bucket(bucket_id, file_id, db)
#     if not file:
#         raise HTTPException(status_code=404, detail="Файл не найден")
#
#     file.status_id = FileStatusEnum.DELETE
#     await db.commit()
#     await db_manager.close_session()
#     log("FILE_API", f"Файл {file.filename}({file_id}) помечен для удаления")
#     return {"id": file.id}
