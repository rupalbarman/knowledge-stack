# knowledge-stack

Content storage solution backed by a vector store for agentic needs

## Table of contents

- [Architecture](#architecture)
  - [file-api](#file-api)
  - [file-worker](#file-worker)
  - [Service split and scalability](#service-split-and-scalability)
- [Development](#development)
- [Data storage](#data-storage)
  - [Files (S3 / RustFS)](#files-s3--rustfs)
  - [Vectors (Milvus)](#vectors-milvus)

## Architecture

Two services, connected via a Redis-backed job queue ([`saq`](https://github.com/tobymao/saq))

### file-api

- FastAPI app - called by a client
- Handles sync operations
  - Authentication
  - CRUD on file and folder
  - Uploading/downloading file bytes to/from RustFS (S3)
  - Vector search (dense, sparse and hybrid)
  - Enqueuing async jobs downstream processing of files

### file-worker

- `SAQ` worker process that runs the actual content pipeline
  - Downloading a file's bytes from RustFS
  - Extracting text content (normalizes to markdown)
  - Chunking
  - Embedding
  - Upserting content vectors into Milvus
  - Also handles vector cleanup jobs on file delete.

### Service split and scalability

- Both `file-api` and `file-worker` are isolated separate applications that only ever communicate via `saq` jobs over Redis.
- They both contain their own dependencies despite having a similar `Dockerfile`
- Scale `file-worker` by adding more replicas - they all pull from the same `saq` queue, no coordination needed.
- Scaling `file-api` isn't as simple as adding replicas, since each one binds its own port. It needs a reverse proxy in front to load-balance requests across replicas.

## Development

- Copy default configuration
  - `cp .env.example .env`
- Run the dependent services
  - `docker compose -f docker-compose.dev.yml up -d`
- Run the application services
  - `docker compose up -d`
  - OR
  - `cd file-api && uvicorn app.main:main`
  - `cd file-worker && saq worker.main.settings -v`
- To use the simple Dev UI for quick view of files, folders and tasks of a user / project
  - Update JWT token at `file-api/static/app.js`
  - Re-run `file-api` and navigate to `/ui`
- To monitor queues, the dashboard is provided by `SAQ` and can be accessed by navigating to `/monitor`

## Data storage

Both, the content files and Milvus object storage use S3 compliant storage system (RustFS)

### Files (S3 / RustFS)

- Everything lives in **one shared bucket**.
- Each file is saved under a key like `<project_id>/<file_id>`.
- Privacy and data isolation is handled by the app, not storage. Storage only ever gets touched after app authentication passes.
- Folders are abstract objects and their association to files are managed by the app / postgres.

### Vectors (Milvus)

- Each project gets its **own Milvus collection**
- Inside a project's collection, each folder is a **partition key** value. This allows scoped searches to allow searches within "folders". Refer Milvus documentation for additional information.
- Files not belonging to any folder, i.e. present in project root get a special folder partition key.
- Milvus only ever holds vectors and a bit of metadata. It is not a source of truth. The real files live in storage (S3 / RustFS) and the real records live in Postgres - allowing rebuilding Milvus record easier.
