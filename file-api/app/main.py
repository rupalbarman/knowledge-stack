from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from saq.web.starlette import saq_web

from app import db, milvus_client
from app.config import settings
from app.migrate import run_migrations
from app.queue import queue
from app.routers import analytics, auth, files, folders, search, tasks, users
from app.storage import ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    await queue.connect()
    await run_migrations()
    await db.connect()
    await ensure_bucket()
    await milvus_client.connect()
    yield
    await milvus_client.disconnect()
    await db.disconnect()
    await queue.disconnect()


app = FastAPI(title="file-api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.cors_allowed_origins.split(",")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/monitor", saq_web("/monitor", queues=[queue]))

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(folders.router)
app.include_router(files.router)
app.include_router(tasks.router)
app.include_router(search.router)
app.include_router(analytics.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
