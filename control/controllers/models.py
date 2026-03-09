import enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class FileStatusEnum:
    UPLOADING = 1
    ERROR = 2
    ACTIVE = 3
    DELETE = 4


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column()
    status_id: Mapped[int] = mapped_column(ForeignKey("file_status.id"))
    bucket_id: Mapped[int] = mapped_column(ForeignKey("bucket.id"))
    # size: Mapped[float] = mapped_column(nullable=True)
    # md5sum: Mapped[str] = mapped_column()


class FileStatus(Base):
    __tablename__ = "file_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class Chunk(Base):
    __tablename__ = "chunk"

    id: Mapped[str] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"))
    chunk_index: Mapped[int] = mapped_column()


class ChunkStorage(Base):
    __tablename__ = "chunk_storage"

    id: Mapped[int] = mapped_column(primary_key=True)
    storage_id: Mapped[int] = mapped_column(ForeignKey("storage.id"))
    chunk_id: Mapped[str] = mapped_column(ForeignKey("chunk.id"))


class Storage(Base):
    __tablename__ = "storage"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column()
    port: Mapped[str] = mapped_column()


class Bucket(Base):
    __tablename__ = "bucket"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
