-- A task is one processing attempt for a file (e.g. vectorization). Kept as
-- its own table rather than a status column on files so history survives
-- across reprocessing, and so other task types (e.g. delete_vectors) can
-- reuse the same shape later.
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    type TEXT NOT NULL DEFAULT 'vectorize',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'superseded')),
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_tasks_file ON tasks(file_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);

-- Points at the authoritative task for this file. A worker compares its own
-- task_id against this before writing to Milvus, so a stale/superseded task
-- can't clobber output from a newer one. Nullable since files.id must exist
-- before its first task can be created; SET NULL rather than blocking task
-- deletion, since files are the side with the real lifecycle here.
ALTER TABLE files ADD COLUMN latest_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL;
