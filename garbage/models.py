from datetime import datetime

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ------------------- DATA---------------
class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column()
    bucket_id: Mapped[int] = mapped_column(ForeignKey("bucket.id"))
    # size: Mapped[float] = mapped_column(nullable=True)
    # md5sum: Mapped[str] = mapped_column()


class ChunkStatusEnum:
    UPLOADING = 1
    ERROR = 2
    ACTIVE = 3
    DELETE = 4


class ChunkStatus(Base):
    __tablename__ = "chunk_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class Chunk(Base):
    __tablename__ = "chunk"

    id: Mapped[str] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"))
    chunk_index: Mapped[int] = mapped_column()
    chunk_status: Mapped[int] = mapped_column(ForeignKey("chunk_status.id"))


class ChunkStorage(Base):
    __tablename__ = "chunk_storage"

    id: Mapped[int] = mapped_column(primary_key=True)
    storage_id: Mapped[int] = mapped_column(ForeignKey("storage.id"))
    chunk_id: Mapped[str] = mapped_column(ForeignKey("chunk.id"))


class Storage(Base):
    __tablename__ = "storage"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column()
    port: Mapped[int] = mapped_column()
    access_key: Mapped[str] = mapped_column()
    secret_key: Mapped[str] = mapped_column()


class Bucket(Base):
    __tablename__ = "bucket"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


# --------------------- LOGGING--------------
class ActionTypeEnum:
    ADD = 1
    REMOVE = 2
    UPLOAD = 3
    DOWNLOAD = 4
    INITIALIZE = 5
    STOP = 6
    MARK_DELETE = 7


class Action(Base):
    __tablename__ = "action"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()


class EntityTypeEnum:
    FILE = 1
    CHUNK = 2
    STORAGE = 3
    SYSTEM = 4
    BUCKET = 5


class EntityType(Base):
    __tablename__ = "entity_type"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class Entity(Base):
    __tablename__ = "entity"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    type_id: Mapped[int] = mapped_column(ForeignKey("entity_type.id"))


class Log(Base):
    __tablename__ = "log"
    id: Mapped[int] = mapped_column(primary_key=True)
    action_id: Mapped[int] = mapped_column(ForeignKey("action.id"))
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"))
    description: Mapped[str] = mapped_column()
    datetime: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text('NOW()'))
    success: Mapped[bool] = mapped_column()
