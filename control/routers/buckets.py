import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from control.DatabaseController import get_db, db_manager, commit_session, create_bucket, get_buckets_list, \
    delete_bucket

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


class BucketRequest(BaseModel):
    bucket_name: str


@router.post("/")
async def add_bucket(bucket: BucketRequest, db: AsyncSession = Depends(get_db)):
    bucket_name = bucket.bucket_name

    session = await db_manager.get_session()

    buckets = await get_buckets_list(session)
    if bucket_name in [b.name for b in buckets]:
        raise HTTPException(status_code=409, detail=f"В системе уже есть бакет {bucket_name}")

    await create_bucket(bucket_name, session)
    await commit_session(session)
    await db_manager.close_session()
    return 201


@router.delete("/{bucket_id}")
async def remove_bucket(bucket_id: int):
    session = await db_manager.get_session()

    buckets = await get_buckets_list(session)
    if bucket_id not in [b.id for b in buckets]:
        raise HTTPException(status_code=400, detail=f"В системе нет бакета с id={bucket_id}")

    await delete_bucket(bucket_id, session)
    await commit_session(session)
    await db_manager.close_session()
    return 200

