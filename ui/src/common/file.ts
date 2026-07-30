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
  // Status of the file's latest constructive task (upsert_vectors). Null
  // means no such task exists at all (not "still pending" - that's its own
  // status value). See file-api FileOut for the full explanation.
  indexing_status: TaskStatus | null;
};
