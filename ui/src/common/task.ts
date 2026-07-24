export type TaskType = "upsert_vectors" | "delete_vectors";
export type TaskReason = "upload" | "manual" | "delete";
export type TaskStatus =
  "pending" | "processing" | "completed" | "failed" | "superseded";

export type TaskObject = {
  id: string;
  project_id: string;
  file_ref: string;
  file_name: string;
  type: TaskType;
  reason: TaskReason;
  status: TaskStatus;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type TaskPageResponse = {
  items: TaskObject[];
  total: number;
  limit: number;
  offset: number;
};
