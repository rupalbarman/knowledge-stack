import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { FolderTree } from '@/components/folder-tree'
import { Sidebar } from '@/components/sidebar'

export type AppLayoutContext = {
  selectedFolderId: string | null
}

// Persistent shell for every authenticated page - the sidebar/folder
// selection lives here so it survives navigating between pages, rather than
// each page owning its own copy. Pages read selectedFolderId via
// useOutletContext<AppLayoutContext>().
export function AppLayout() {
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(
    null,
  )

  return (
    <div className="flex h-screen">
      <Sidebar>
        <FolderTree
          selectedFolderId={selectedFolderId}
          onSelectFolder={(folderId) => setSelectedFolderId(folderId)}
        />
      </Sidebar>

      <div className="flex-1 overflow-hidden">
        <Outlet
          context={{ selectedFolderId } satisfies AppLayoutContext}
        />
      </div>
    </div>
  )
}
