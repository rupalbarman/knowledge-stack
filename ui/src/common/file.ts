export type FileObject = {
  id: string;
  project_id: string;
  folder_id: string | null;
  name: string;
  content_type: string | null;
  size_bytes: number;
  storage_key: string;
  created_at: string;
};
