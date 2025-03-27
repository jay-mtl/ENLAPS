import contextlib
from fastapi import FastAPI
import logging
from typing import Any, AsyncGenerator
from alembic.config import Config
from alembic import command
import asyncio


from api.settings import settings
from api.routers.tikeePictures import router as tikeepictures_router


log = logging.getLogger("uvicorn")


async def run_migrations():
    alembic_cfg = Config("alembic.ini")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    log.info("Starting up...")
    log.info("run alembic upgrade head...")
    await run_migrations()

    if settings.debug:
        print(settings)
    yield

    log.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

app.include_router(
    tikeepictures_router,
    prefix="/tikeepictures",
    tags=["tikeepictures"],
)
