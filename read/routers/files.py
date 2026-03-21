from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from write.controllers.DatabaseController import get_db, db_manager, add_file_info, commit_session, \
    get_file_in_bucket, get_files_by_bucket
from write.controllers.StorageContoller import get_most_relevant, find_online_nodes, process_file_upload
from write.controllers.models import File, FileStatusEnum
from control.log import log

router = APIRouter(
    prefix="/file",
    tags=["File"]
)


@router.get("/{bucket_id}")
async def get_files_in_bucket(bucket_id: int, db: AsyncSession = Depends(get_db)):
    return await get_files_by_bucket(bucket_id, db)

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
