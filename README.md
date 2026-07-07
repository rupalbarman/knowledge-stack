# knowledge-stack
Content storage solution backed by a vector store for agentic needs

## Known caveats / follow-ups

- **Orphaned RustFS objects on file-create rollback** (`file-api/app/routers/files.py`,
  `create_file`): the object upload to RustFS happens *before* the Postgres
  transaction that inserts the `files`/`tasks` rows. If that transaction rolls
  back (e.g. a duplicate filename, or any error inserting the task), the
  already-uploaded bytes are left in RustFS with no DB row ever pointing at
  them - a harmless but real storage leak. RustFS isn't a participant in the
  Postgres transaction, so this can't be fixed with `conn.transaction()`
  alone; would need either a reconciliation/GC job that sweeps
  orphaned keys, or reordering to upload only after the DB rows are committed
  (at the cost of a race where a committed file row briefly has no object
  behind it).
