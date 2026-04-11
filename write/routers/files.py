from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from write.log import log
from write.controllers.database_controller import get_db, db_manager, add_file_info, commit_session, \
    get_file_in_bucket, get_files_by_bucket, set_file_to_delete
from write.controllers.models import File, EntityTypeEnum, ActionTypeEnum
from write.controllers.storage_controller import get_most_relevant, process_file_upload

router = APIRouter(
    prefix="/file",
    tags=["File"]
)


@router.get("/{bucket_id}")
async def get_files_in_bucket(bucket_id: int, session: AsyncSession = Depends(get_db)):
    return await get_files_by_bucket(bucket_id, session)


# TODO() Think about adding file, chunk, chunk_storage data into controllers only after its writing
@router.post("/{bucket_id}")
async def upload_file(bucket_id: int, file: UploadFile, session: AsyncSession = Depends(get_db)):
    original_name = file.filename

    target_nodes = await get_most_relevant()

    if not target_nodes:
        raise HTTPException(status_code=503, detail="Нет доступных нод")

    # log("FILE_API", f"Начита загрузка файла: {original_name}")
    new_file = File(filename=original_name, bucket_id=bucket_id)
    try:
        await add_file_info(new_file, session)
        result = await process_file_upload(file, original_name, target_nodes, session)
        # new_file.status_id = FileStatusEnum.ACTIVE

        await log(
            entity_name=f"{file.filename}",
            entity_type=EntityTypeEnum.FILE,
            action=ActionTypeEnum.UPLOAD,
            description="",
            success=True,
            session=session
        )
        return {
            "filename": original_name,
            "bucket_id": bucket_id,
            "chunks": result['total_chunks'],
            "nodes": target_nodes,
            "status": "success"
        }

    except Exception as e:
        # new_file.status_id = FileStatusEnum.ERROR
        # log("FILE_API", f"Ошибка при сохранении блоков файла {file.filename}")
        await log(
            entity_name=f"{file.filename}",
            entity_type=EntityTypeEnum.FILE,
            action=ActionTypeEnum.UPLOAD,
            description="Ошибка при сохранении блоков файла",
            success=False,
            session=session
        )
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении блоков: {str(e)}")
    finally:
        await commit_session(session)
        await db_manager.close_session()


@router.delete("/{file_id}")
async def delete_file(file_id: int, session: AsyncSession = Depends(get_db)):

    file = await get_file_in_bucket(file_id, session)
    if not file:
        raise HTTPException(status_code=404, detail="Файл не найден")

    await set_file_to_delete(file_id, session)
    await log(
        entity_name=f"{file.filename}",
        entity_type=EntityTypeEnum.FILE,
        action=ActionTypeEnum.MARK_DELETE,
        description="",
        success=True,
        session=session
    )
    await commit_session(session)
    await db_manager.close_session()

    # log("FILE_API", f"Файл {file.filename}({file_id}) помечен для удаления")
    return {"id": file.id}