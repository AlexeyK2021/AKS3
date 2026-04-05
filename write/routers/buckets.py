from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from write.controllers.DatabaseController import get_db, db_manager, get_buckets_list

router = APIRouter(
    prefix="/bucket",
    tags=["Bucket"]
)


@router.get("/")
async def get_buckets(db: AsyncSession = Depends(get_db)):
    buckets = await get_buckets_list(db)
    await db_manager.close_session()
    return {"buckets": buckets}