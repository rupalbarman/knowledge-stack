import type { FileObject } from '@/common'
import { fileHooks } from '@/hooks/file-hooks'

type FileListProps = {
  folderId: string | null
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1024
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`
}

// Kept as its own component rather than inlined into the table body - file
// display will likely be reworked/extended later, and this keeps that change
// contained without restructuring FileList itself.
function FileListItem({ file }: { file: FileObject }) {
  return (
    <tr className="border-border border-b">
      <td className="px-3 py-2 text-sm">{file.name}</td>
      <td className="text-muted-foreground px-3 py-2 text-sm">
        {file.content_type ?? '-'}
      </td>
      <td className="text-muted-foreground px-3 py-2 text-sm">
        {formatBytes(file.size_bytes)}
      </td>
      <td className="text-muted-foreground px-3 py-2 text-sm">
        {new Date(file.created_at).toLocaleString()}
      </td>
    </tr>
  )
}

export function FileList({ folderId }: FileListProps) {
  const { data, isLoading, isError } = fileHooks.useFilesByFolder(folderId)

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading files...</p>
  }

  if (isError) {
    return <p className="text-destructive text-sm">Failed to load files.</p>
  }

  if (!data || data.length === 0) {
    return <p className="text-muted-foreground text-sm">No files</p>
  }

  return (
    <table className="w-full text-left">
      <thead>
        <tr className="border-border border-b text-sm font-medium">
          <th className="px-3 py-2">Name</th>
          <th className="px-3 py-2">Content type</th>
          <th className="px-3 py-2">Size</th>
          <th className="px-3 py-2">Created</th>
        </tr>
      </thead>
      <tbody>
        {data.map((file) => (
          <FileListItem key={file.id} file={file} />
        ))}
      </tbody>
    </table>
  )
}
