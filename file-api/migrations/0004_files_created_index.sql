-- Supports GET /files/recent (project-scoped, ordered by created_at, paginated).
-- Mirrors idx_tasks_project_created, which serves the identical access
-- pattern on tasks.
CREATE INDEX idx_files_project_created ON files(project_id, created_at DESC);
