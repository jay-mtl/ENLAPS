from typing import Optional

from pydantic import BaseModel


class TikeePictureBase(BaseModel):
    s3_key: str
    resolution: str
    file_size: int
    shooting_date: str
    metadata: Optional[dict[str, str | float]] = None

    class Config:
        from_attributes = True


class TikeePictureCreate(TikeePictureBase):
    pass


class TikeePictureDB(TikeePictureBase):
    id: str
    tikee_uuid: str
    sequence: str
