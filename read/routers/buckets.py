from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.database_controller import get_db, db_manager, get_buckets_list

router = APIRouter(
    prefix="/bucket",
    tags=["Bucket"]
)


@router.get("/")
async def get_buckets(db: AsyncSession = Depends(get_db)):
    session = await db_manager.get_session()
    buckets = await get_buckets_list(session)

    await db_manager.close_session()
    return {"buckets": buckets}
