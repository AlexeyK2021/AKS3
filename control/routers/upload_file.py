from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from control.controllers.DatabaseController import get_db, db_manager, rollback_session, save_file_info, commit_session
from control.controllers.StorageContoller import get_most_relevant, find_online_nodes, process_file_upload, \
    delete_chunks

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
    try:
        await save_file_info(original_name, session)
        result = await process_file_upload(file, original_name, target_nodes, session)
        await commit_session(session)
        await db_manager.close_session()

        return {
            "filename": original_name,
            "chunks": result['total_chunks'],
            "nodes": target_nodes,
            "status": "success"
        }

    except Exception as e:
        # await delete_chunks(original_name, target_nodes, session)
        await rollback_session(session)
        await db_manager.close_session()
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении блоков: {str(e)}")
