from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from control.controllers.DatabaseController import get_db, db_manager, rollback_session, add_file_info, commit_session
from control.controllers.StorageContoller import get_most_relevant, find_online_nodes, process_file_upload
from control.controllers.models import FileMetadata

router = APIRouter(
    prefix="/file",
    tags=["File"]
)


# TODO() Think about adding file, chunk, chunk_storage data into controllers only after its writing
@router.post("/upload")
async def upload_file(file: UploadFile, db: AsyncSession = Depends(get_db)):
    original_name = file.filename

    target_nodes = await get_most_relevant(await find_online_nodes(db))

    if not target_nodes:
        raise HTTPException(status_code=503, detail="Нет доступных нод")

    print(f"Начита загрузка файла: {original_name}")
    session = await db_manager.get_session()
    new_file = FileMetadata(filename=original_name, status_id=1)
    try:
        await add_file_info(new_file, session)
        result = await process_file_upload(file, original_name, target_nodes, session)
        new_file.status_id = 3

        return {
            "filename": original_name,
            "chunks": result['total_chunks'],
            "nodes": target_nodes,
            "status": "success"
        }

    except Exception as e:
        # await delete_chunks(original_name, target_nodes, session)
        new_file.status_id = 2
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении блоков: {str(e)}")
    finally:
        await commit_session(session)
        await db_manager.close_session()
