import { FileDataTable } from "@/components/file-data-table";
import { fileHooks } from "@/hooks/file-hooks";

const RECENT_FILES_PAGE_SIZE = 50;

export function RecentFilesTable() {
  const { data, isLoading, isError } = fileHooks.useRecentFiles(
    RECENT_FILES_PAGE_SIZE,
  );

  return (
    <div className="space-y-3">
      <h2 className="text-base font-semibold">Recent Documents</h2>
      <FileDataTable
        data={data?.items}
        isLoading={isLoading}
        isError={isError}
      />
    </div>
  );
}
