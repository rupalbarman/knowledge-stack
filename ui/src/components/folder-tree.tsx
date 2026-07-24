import type { FolderTreeNode } from '@/common'
import { folderHooks } from '@/hooks/folder-hooks'
import { cn } from '@/lib/utils'

type FolderTreeProps = {
  selectedFolderId: string | null
  onSelectFolder: (folderId: string | null, folderName: string) => void
}

type FolderTreeItemProps = {
  node: FolderTreeNode
  depth: number
  selectedFolderId: string | null
  onSelectFolder: (folderId: string | null, folderName: string) => void
}

function FolderTreeRow({
  label,
  depth,
  isSelected,
  onSelect,
}: {
  label: string
  depth: number
  isSelected: boolean
  onSelect: () => void
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onSelect()
        }
      }}
      style={{ paddingLeft: `${0.5 + depth}rem` }}
      className={cn(
        'cursor-pointer rounded-md py-1.5 pr-2 text-sm select-none',
        isSelected
          ? 'bg-accent text-accent-foreground font-medium'
          : 'hover:bg-accent/50',
      )}
    >
      {label}
    </div>
  )
}

function FolderTreeItem({
  node,
  depth,
  selectedFolderId,
  onSelectFolder,
}: FolderTreeItemProps) {
  return (
    <li>
      <FolderTreeRow
        label={node.name}
        depth={depth}
        isSelected={selectedFolderId === node.id}
        onSelect={() => onSelectFolder(node.id, node.name)}
      />
      {node.children.length > 0 && (
        <ul>
          {node.children.map((child) => (
            <FolderTreeItem
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedFolderId={selectedFolderId}
              onSelectFolder={onSelectFolder}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

export function FolderTree({
  selectedFolderId,
  onSelectFolder,
}: FolderTreeProps) {
  const { data, isLoading, isError } = folderHooks.useFolderTree()

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">Loading folders...</p>
  }

  if (isError) {
    return <p className="text-destructive text-sm">Failed to load folders.</p>
  }

  return (
    <ul className="space-y-0.5">
      <li>
        <FolderTreeRow
          label="(root)"
          depth={0}
          isSelected={selectedFolderId === null}
          onSelect={() => onSelectFolder(null, '(root)')}
        />
      </li>
      {data?.map((node) => (
        <FolderTreeItem
          key={node.id}
          node={node}
          depth={1}
          selectedFolderId={selectedFolderId}
          onSelectFolder={onSelectFolder}
        />
      ))}
    </ul>
  )
}
