import type { TaskStatus } from "./task";

export type FileObject = {
  id: string;
  project_id: string;
  folder_id: string | null;
  name: string;
  content_type: string | null;
  size_bytes: number;
  storage_key: string;
  created_at: string;
  // Status of the file's latest constructive task (upsert_vectors). Nullable
  // in case it was never processed. Refer relevant file-api File model.
  indexing_status: TaskStatus | null;
};
