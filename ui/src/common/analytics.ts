export type DocumentStatusBreakdown = {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
};

export type AnalyticsSummary = {
  total_documents: number;
  total_folders: number;
  storage_used_bytes: number;
  total_chunks: number;
  documents_by_status: DocumentStatusBreakdown;
};
