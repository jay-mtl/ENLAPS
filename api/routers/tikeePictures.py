from collections.abc import Sequence
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


from api.database.db import get_async_session
from api.database import tables
from api.models.tikeePicture import (
    TikeePictureCreate,
    TikeePictureDB,
)

router = APIRouter()


async def get_pictures_from_tikeeuuid_and_sequence(
    tikee_uuid: str,
    sequence: str,
    session: AsyncSession = Depends(get_async_session),
) -> Sequence[tables.TikeePictures] | None:
    select_query = select(tables.TikeePictures).where(
        and_(
            tables.TikeePictures.tikee_uuid == tikee_uuid,
            tables.TikeePictures.sequence == sequence,
        )
    )

    result = await session.execute(select_query)
    tikee_pictures = result.scalars().all()

    if tikee_pictures is None:
        return None

    return tikee_pictures


def stiching_service(
    tikeepicture: TikeePictureCreate,
    picture_name: str,
    picture_type: str,
    tikee_pictures: Sequence[tables.TikeePictures] | None,
) -> None:
    def filter_picture(picture: tables.TikeePictures) -> bool:
        if picture_name != picture.s3_key.split(sep="/")[3]:
            return False

        if (
            picture_type == picture.s3_key.split(sep="/")[2]
            or picture_type == "stiched"
        ):
            return False

        return True

    if tikee_pictures:
        previous_pictures = filter(filter_picture, tikee_pictures)
        if len(list(previous_pictures)) == 1:
            print(f"{tikeepicture.s3_key} has been sent to the stitching service")


@router.post(
    "",
    response_model=TikeePictureDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_tikeepicture(
    tikeepicture: TikeePictureCreate,
    session: AsyncSession = Depends(get_async_session),
) -> TikeePictureDB:
    tikeepicture = TikeePictureCreate(**tikeepicture.model_dump())

    list_uuid_sequence = tikeepicture.s3_key.split(sep="/")
    tikee_uuid = list_uuid_sequence[0]
    sequence = list_uuid_sequence[1]
    picture_type = list_uuid_sequence[2]
    picture_name = list_uuid_sequence[3]

    tikee_pictures = await get_pictures_from_tikeeuuid_and_sequence(
        tikee_uuid, sequence, session
    )

    if tikee_pictures:
        if tikee_pictures[0].resolution != tikeepicture.resolution:
            raise HTTPException(
                detail=(
                    f"The resolution for the sequence {sequence} need to be {tikee_pictures[0].resolution}, "
                    f"but got {tikeepicture.resolution} "
                    f"for the s3_key {tikeepicture.s3_key}"
                ),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    tikeepicture_id = uuid.uuid4()

    session.add(
        tables.TikeePictures(
            id=str(tikeepicture_id),
            tikee_uuid=tikee_uuid,
            sequence=sequence,
            **tikeepicture.model_dump(),
            metadata_=tikeepicture.metadata,
        )
    )

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            detail=(f"{e.args[0]}, \n for the s3_key {tikeepicture.s3_key}"),
            status_code=status.HTTP_409_CONFLICT,
        )

    stiching_service(tikeepicture, picture_name, picture_type, tikee_pictures)

    # def filter_picture(picture: tables.TikeePictures) -> bool:
    #     if picture_name != picture.s3_key.split(sep="/")[3]:
    #         return False

    #     if (
    #         picture_type == picture.s3_key.split(sep="/")[2]
    #         or picture_type == "stiched"
    #     ):
    #         return False

    #     return True

    # if tikee_pictures:
    #     previous_pictures = filter(filter_picture, tikee_pictures)
    #     if len(list(previous_pictures)) == 1:
    #         print(f"{tikeepicture.s3_key} has been sent to the stitching service")

    return TikeePictureDB(
        id=str(tikeepicture_id),
        tikee_uuid=tikee_uuid,
        sequence=sequence,
        **tikeepicture.model_dump(),
    )
