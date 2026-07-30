-- Task denotes any job deffered to the worker over the queue and
-- serves not only as a queue message but also as an audit trail.
--
-- file_ref is not a FK, hence not being a file_id. This is to ensure that references remain
-- even if the file is deleted. Serving as an audit log.
-- project_id is a FK and if deleted, it would delete all associated tasks as well.
-- reason denotes the reason the entry was created
-- type denotes the type of worker job to run
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_ref UUID NOT NULL,
    file_name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'upsert_vectors'
        CHECK (type IN ('upsert_vectors', 'delete_vectors')),
    reason TEXT NOT NULL CHECK (reason IN ('upload', 'manual', 'delete', 'replace')),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'superseded')),
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Supports GET /tasks (project-scoped, ordered by created_at, paginated)
CREATE INDEX idx_tasks_project_created ON tasks(project_id, created_at DESC);
-- Supports GET /tasks?file_id=... (project + file scoped, ordered by created_at, paginated)
CREATE INDEX idx_tasks_project_file_created ON tasks(project_id, file_ref, created_at DESC);

-- latest_task_id represents the latest "constructive" task, i.e. creating a vector.
-- This is to ensure worker only picks up latest change and ignores any in-flight updates to
-- avoid wasteful computation/extraction.
ALTER TABLE files ADD COLUMN latest_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL;
