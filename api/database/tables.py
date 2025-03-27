from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSON

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TikeePictures(Base):
    __tablename__ = "tikee_pictures"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tikee_uuid: Mapped[str] = mapped_column(String, index=True)
    sequence: Mapped[str] = mapped_column(String, index=True)
    s3_key: Mapped[str] = mapped_column(String, unique=True)
    resolution: Mapped[str] = mapped_column(String)
    file_size: Mapped[int] = mapped_column(Integer)
    shooting_date: Mapped[str] = mapped_column(String)
    metadata_: Mapped[dict[str, str | float] | None] = mapped_column(
        JSON, name="metadata"
    )
