from controllers.database_controller import get_db, db_manager, commit_session, db_create_bucket, \
    db_get_buckets_list, \
    db_delete_bucket
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from log import log
from controllers.models import EntityTypeEnum, ActionTypeEnum

router = APIRouter(
    prefix="/bucket",
    tags=["Bucket"]
)


@router.get("/")
async def get_buckets(db: AsyncSession = Depends(get_db)):
    buckets = await db_get_buckets_list(db)

    await db_manager.close_session()
    return {"buckets": buckets}


class BucketRequest(BaseModel):
    bucket_name: str


@router.post("/")
async def add_bucket(bucket: BucketRequest, session: AsyncSession = Depends(get_db)):
    bucket_name = bucket.bucket_name

    buckets = await db_get_buckets_list(session)
    if bucket_name in [b.name for b in buckets]:
        await log(
            entity_name=f"{bucket.bucket_name}",
            entity_type=EntityTypeEnum.BUCKET,
            action=ActionTypeEnum.ADD,
            description="В системе уже есть такой бакет",
            success=False,
            session=session
        )
        raise HTTPException(status_code=409, detail=f"В системе уже есть бакет {bucket_name}")

    await db_create_bucket(bucket_name, session)
    await log(
        entity_name=f"{bucket.bucket_name}",
        entity_type=EntityTypeEnum.BUCKET,
        action=ActionTypeEnum.ADD,
        description="",
        success=True,
        session=session
    )
    await commit_session(session)
    await db_manager.close_session()
    return 201


@router.delete("/{bucket_id}")
async def remove_bucket(bucket_id: int, session: AsyncSession = Depends(get_db)):

    buckets = await db_get_buckets_list(session)
    if bucket_id not in [b.id for b in buckets]:
        await log(
            entity_name=f"{bucket_id}",
            entity_type=EntityTypeEnum.BUCKET,
            action=ActionTypeEnum.REMOVE,
            description="В системе нет бакета",
            success=False,
            session=session
        )
        raise HTTPException(status_code=400, detail=f"В системе нет бакета с id={bucket_id}")

    await db_delete_bucket(bucket_id, session)
    await log(
        entity_name=f"{bucket_id}",
        entity_type=EntityTypeEnum.BUCKET,
        action=ActionTypeEnum.REMOVE,
        description="",
        success=True,
        session=session
    )
    await commit_session(session)
    await db_manager.close_session()
    return 200
