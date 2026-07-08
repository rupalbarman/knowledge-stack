# knowledge-stack

Content storage solution backed by a vector store for agentic needs

## Data storage

Two different stores, for two different jobs.

### Files (S3 / RustFS)

- Everything lives in **one shared bucket**. There's no per-project or per-user bucket.
- Each file is saved under a key like `<project_id>/<file_id>`.
- Privacy and data isolation is handled entirely by the app, not storage. Storage only ever gets touched after app authentication passes.
- Folders are abstract objects and their associated to files are managed entirely by the app / postgres.

### Vectors (Milvus)

- Each project (tenant) gets its **own Milvus collection**
- Inside a project's collection, each folder is a **partition key** value. This lets a search scoped to one folder skip over every other folder's data, without needing to create a separate partition per folder (which would run into Milvus hard limit on partitions per collection).
- Files sitting at a project's root (not inside any folder) get a placeholder folder value instead of "no folder," so they still fit the same scheme cleanly.
- Milvus only ever holds vectors and a bit of metadata (project id, folder id, file id, chunk text) - it's a derived index, not a source of truth. The real files live in storage (S3 / RustFS) and the real records live in Postgres, so Milvus data can always be rebuilt from scratch by reprocessing files if it's ever wiped or restructured.

## Known caveats / follow-ups

- **Orphaned RustFS objects on file-create rollback** (`file-api/app/routers/files.py`,
  `create_file`): the object upload to RustFS happens _before_ the Postgres
  transaction that inserts the `files`/`tasks` rows. If that transaction rolls
  back (e.g. a duplicate filename, or any error inserting the task), the
  already-uploaded bytes are left in RustFS with no DB row ever pointing at
  them - a harmless but real storage leak. RustFS isn't a participant in the
  Postgres transaction, so this can't be fixed with `conn.transaction()`
  alone; would need either a reconciliation/GC job that sweeps
  orphaned keys, or reordering to upload only after the DB rows are committed
  (at the cost of a race where a committed file row briefly has no object
  behind it).
