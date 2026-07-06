from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db
from app.migrate import run_migrations
from app.queue import queue
from app.routers import auth, files, folders, users
from app.storage import ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    await queue.connect()
    await run_migrations()
    await db.connect()
    await ensure_bucket()
    yield
    await db.disconnect()
    await queue.disconnect()


app = FastAPI(title="file-api", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(folders.router)
app.include_router(files.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
