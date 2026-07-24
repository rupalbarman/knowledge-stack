import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Dialog } from 'radix-ui'
import { FolderTree } from '@/components/folder-tree'
import { Sidebar } from '@/components/sidebar'
import { useTheme } from '@/components/theme-provider'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'

function useWiringCheck() {
  return useQuery({
    queryKey: ['wiring-check'],
    queryFn: async () => {
      await new Promise((resolve) => setTimeout(resolve, 300))
      return 'TanStack Query is wired up.'
    },
  })
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex gap-2">
      {(['light', 'dark', 'system'] as const).map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => setTheme(option)}
          className={`rounded-md border px-3 py-1.5 text-sm font-medium ${
            theme === option
              ? 'bg-primary text-primary-foreground border-primary'
              : 'border-border text-foreground'
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  )
}

export function HomePage() {
  const { data, isLoading } = useWiringCheck()
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

      <div className="bg-background text-foreground flex flex-1 flex-col items-center justify-center gap-4 overflow-y-auto">
        <p className="border-border bg-card text-card-foreground rounded-md border px-6 py-4 text-lg font-medium shadow">
          {isLoading ? 'Loading...' : data}
        </p>

        <ThemeToggle />

        <Tooltip>
          <TooltipTrigger className="bg-secondary text-secondary-foreground rounded-md px-4 py-2 text-sm font-medium">
            Hover me
          </TooltipTrigger>
          <TooltipContent>Tooltip is wired up.</TooltipContent>
        </Tooltip>

        <Dialog.Root>
          <Dialog.Trigger className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium">
            Open Radix dialog
          </Dialog.Trigger>
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 bg-black/40" />
            <Dialog.Content className="bg-card text-card-foreground fixed top-1/2 left-1/2 w-80 -translate-x-1/2 -translate-y-1/2 rounded-md p-6 shadow-lg">
              <Dialog.Title className="text-base font-semibold">
                Radix UI is wired up.
              </Dialog.Title>
              <Dialog.Close className="bg-secondary text-secondary-foreground mt-4 rounded-md px-4 py-2 text-sm font-medium">
                Close
              </Dialog.Close>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </div>
    </div>
  )
}
