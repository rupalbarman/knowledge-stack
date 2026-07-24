export type FolderTreeNode = {
  id: string;
  name: string;
  children: FolderTreeNode[];
};

export type FolderObject = {
  id: string;
  project_id: string;
  parent_id: string | null;
  name: string;
  created_at: string;
};
