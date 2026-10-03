import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, HTTPException, Request

from .infrai_client import InfraiError, InfraiImageClient
from .models import ThumbnailRequest, ThumbnailResult
from .thumbnail_service import ThumbnailService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    api_key = os.environ["INFRAI_API_KEY"]
    client = InfraiImageClient(api_key)
    app.state.thumbnail_service = ThumbnailService(client)
    yield
    await client.close()


service = FastAPI(title="Nonprofit thumbnail service", lifespan=lifespan)


@service.post("/thumbnails", response_model=ThumbnailResult)
async def create_thumbnail(payload: ThumbnailRequest, request: Request) -> ThumbnailResult:
    thumbnail_service: ThumbnailService = request.app.state.thumbnail_service
    try:
        return await thumbnail_service.generate(payload)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc


def run() -> None:
    uvicorn.run("nonprofit_thumbnails.api:service", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
