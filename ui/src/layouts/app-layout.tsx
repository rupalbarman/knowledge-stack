import { useState } from 'react'
import { ListTodo } from 'lucide-react'
import { Outlet } from 'react-router-dom'

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

  return (
    <div className="flex h-screen">
      <Sidebar>
        <SidebarSection title="Folders">
          <FolderTree
            selectedFolderId={selectedFolderId}
            onSelectFolder={(folderId) => setSelectedFolderId(folderId)}
          />
        </SidebarSection>

        {/* todo: hook up to TasksPage once it exists */}
        <SidebarButton
          icon={<ListTodo className="size-4 shrink-0" />}
          label="Tasks"
          onClick={() => {}}
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
