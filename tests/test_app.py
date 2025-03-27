import asyncio
from collections.abc import AsyncGenerator
import httpx
import pytest

from asgi_lifespan import LifespanManager
from fastapi import status
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import uuid


from api.app import app
from api.models.tikeePicture import TikeePictureCreate
from api.database import tables
from api.database.db import get_async_session
from api.database.tables import Base


DATABASE_URL = "postgresql+asyncpg://test:test@localhost/tikeePictures_test"
engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def get_test_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_async_session] = get_test_async_session
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://app.io",
        ) as test_client:
            yield test_client


@pytest_asyncio.fixture(autouse=True, scope="module")
async def initialize_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    initials_pictures = [
        TikeePictureCreate(
            s3_key="677c082c-3a1a-44d9-874a-20169546c653/123456789/left/my_photo.jpg",
            resolution="4096x1862",
            file_size=456874,
            shooting_date="2021-07-16 11:33:10.592579",
            metadata={
                "GPSLatitude": 0.34,
                "GPSLongitude": 0.45,
                "GPSAltitude": 0.78,
                "Camera Model Name": "TIKEE",
                "Make": "ENLAPS",
            },
        ),
        TikeePictureCreate(
            s3_key="677c082c-3a1a-44d9-874a-20169546c653/123456789/right/my_photo.jpg",
            resolution="4096x1862",
            file_size=456874,
            shooting_date="2021-07-16 11:33:10.592579",
            metadata={
                "GPSLatitude": 0.34,
                "GPSLongitude": 0.45,
                "GPSAltitude": 0.78,
                "Camera Model Name": "TIKEE",
                "Make": "ENLAPS",
            },
        ),
        TikeePictureCreate(
            s3_key="677c082c-3a1a-44d9-874a-20169546c653/123456789/left/my_photo1.jpg",
            resolution="4096x1862",
            file_size=456874,
            shooting_date="2021-07-16 11:33:10.592579",
            metadata={
                "GPSLatitude": 0.34,
                "GPSLongitude": 0.45,
                "GPSAltitude": 0.78,
                "Camera Model Name": "TIKEE",
                "Make": "ENLAPS",
            },
        ),
    ]

    async with async_session_maker() as session:
        for picture in initials_pictures:
            list_uuid_sequence = picture.s3_key.split(sep="/")[:2]
            tikee_uuid = list_uuid_sequence[0]
            sequence = list_uuid_sequence[1]
            tikeepicture_id = uuid.uuid4()

            session.add(
                tables.TikeePictures(
                    id=str(tikeepicture_id),
                    tikee_uuid=tikee_uuid,
                    sequence=sequence,
                    **picture.model_dump(by_alias=True),
                    metadata_=picture.metadata,
                )
            )

        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
class TestCreateTikeePicture:
    async def test_invalid_payload_missing_shooting_date(
        self, client: httpx.AsyncClient
    ):
        payload = {
            "s3_key": "677c082c-3a1a-44d9-874a-20169546c653/123456790/left/my_photo.jpg",
            "resolution": "4096x1862",
            "file_size": 456874,
            "metadata": {
                "GPSLatitude": 0.34,
                "GPSLongitude": 0.45,
                "GPSAltitude": 0.78,
                "Camera Model Name": "TIKEE",
                "Make": "ENLAPS",
            },
        }

        response = await client.post("/tikeepictures", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_invalid_payload_wrong_resolution(self, client: httpx.AsyncClient):
        payload = {
            "s3_key": "677c082c-3a1a-44d9-874a-20169546c653/123456789/right/my_photo_1.jpg",
            "resolution": "4096x480",
            "file_size": 456874,
            "shooting_date": "2021-07-16 11:33:10.592579",
            "metadata": {
                "GPSLatitude": 0.34,
                "GPSLongitude": 0.45,
                "GPSAltitude": 0.78,
                "Camera Model Name": "TIKEE",
                "Make": "ENLAPS",
            },
        }

        response = await client.post("/tikeepictures", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.text
            == '{"detail":"The resolution for the sequence 123456789 need to be 4096x1862, but got 4096x480 '
            'for the s3_key 677c082c-3a1a-44d9-874a-20169546c653/123456789/right/my_photo_1.jpg"}'
        )

    async def test_valid_payload(self, client: httpx.AsyncClient):
        payload = {
            "s3_key": "677c082c-3a1a-44d9-874a-20169546c653/123456791/left/my_photo.jpg",
            "resolution": "4096x1862",
            "file_size": 456874,
            "shooting_date": "2021-07-16 11:33:10.592579",
            "metadata": {
                "GPSLatitude": 0.34,
                "GPSLongitude": 0.45,
                "GPSAltitude": 0.78,
                "Camera Model Name": "TIKEE",
                "Make": "ENLAPS",
            },
        }

        response = await client.post("/tikeepictures", json=payload)

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        for key in payload:
            assert json[key] == payload[key]

    async def test_valid_payload_stiched(self, client: httpx.AsyncClient, capfd):
        payload = {
            "s3_key": "677c082c-3a1a-44d9-874a-20169546c653/123456789/right/my_photo1.jpg",
            "resolution": "4096x1862",
            "file_size": 456874,
            "shooting_date": "2021-07-16 11:33:10.592579",
            "metadata": {
                "GPSLatitude": 0.34,
                "GPSLongitude": 0.45,
                "GPSAltitude": 0.78,
                "Camera Model Name": "TIKEE",
                "Make": "ENLAPS",
            },
        }

        response = await client.post("/tikeepictures", json=payload)

        assert response.status_code == status.HTTP_201_CREATED

        out, err = capfd.readouterr()
        assert out == f'{payload["s3_key"]} has been sent to the stitching service\n'

        json = response.json()
        for key in payload:
            assert json[key] == payload[key]
