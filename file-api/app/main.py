from contextlib import asynccontextmanager

from fastapi import FastAPI
from saq.web.starlette import saq_web

from app import db, milvus_client
from app.migrate import run_migrations
from app.queue import queue
from app.routers import auth, files, folders, search, tasks, users
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

app.mount("/monitor", saq_web("/monitor", queues=[queue]))

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(folders.router)
app.include_router(files.router)
app.include_router(tasks.router)
app.include_router(search.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
