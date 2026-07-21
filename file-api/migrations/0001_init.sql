-- Every id is supplied by the app uuid4()
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Project is the tenant boundary
-- owner_id is UNIQUE to enforce 1 user <-> 1 project; Might change to accommodate project sharing
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE folders (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE files (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    content_type TEXT,
    size_bytes BIGINT NOT NULL,
    storage_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Postgres UNIQUE constraints treat NULLs as distinct, which would let
-- multiple root-level (parent_id/folder_id IS NULL) entries share a name.
-- Partial indexes cover both the nested and root cases correctly.
CREATE UNIQUE INDEX idx_folders_unique_nested ON folders(project_id, parent_id, name) WHERE parent_id IS NOT NULL;
CREATE UNIQUE INDEX idx_folders_unique_root ON folders(project_id, name) WHERE parent_id IS NULL;
CREATE INDEX idx_folders_project ON folders(project_id);
CREATE INDEX idx_folders_parent ON folders(parent_id);

CREATE UNIQUE INDEX idx_files_unique_nested ON files(project_id, folder_id, name) WHERE folder_id IS NOT NULL;
CREATE UNIQUE INDEX idx_files_unique_root ON files(project_id, name) WHERE folder_id IS NULL;
CREATE INDEX idx_files_project ON files(project_id);
CREATE INDEX idx_files_folder ON files(folder_id);
