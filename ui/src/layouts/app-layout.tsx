import { useState } from 'react'
import { Files, ListTodo } from 'lucide-react'
import { Outlet, useNavigate } from 'react-router-dom'

import { FolderTree } from '@/components/folder-tree'
import { Sidebar, SidebarButton, SidebarSection } from '@/components/sidebar'

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
  const navigate = useNavigate()

  // Jump to relevant files page of the selected folder
  function handleSelectFolder(folderId: string | null) {
    setSelectedFolderId(folderId)
    navigate('/files')
  }

  return (
    <div className="flex h-screen">
      <Sidebar>
        <SidebarButton
          icon={<Files className="size-4 shrink-0" />}
          label="Files"
          onClick={() => handleSelectFolder(null)}
        />

        <SidebarSection title="Folders">
          <FolderTree
            selectedFolderId={selectedFolderId}
            onSelectFolder={handleSelectFolder}
          />
        </SidebarSection>

        <SidebarButton
          icon={<ListTodo className="size-4 shrink-0" />}
          label="Tasks"
          onClick={() => navigate('/tasks')}
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
