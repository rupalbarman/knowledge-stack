import { useState } from 'react'

import { AddContentMenu } from '@/components/add-content-menu'
import { FileDataTable } from '@/components/file-data-table'
import { PageBody } from '@/components/page-body'
import { PageHeader } from '@/components/page-header'
import { SearchBox } from '@/components/search-box'

type FilePageProps = {
  folderId: string | null
}

export function FilePage({ folderId }: FilePageProps) {
  const [highlightedFileId, setHighlightedFileId] = useState<string | null>(
    null,
  )

  function handleHighlightFile(fileId: string) {
    setHighlightedFileId(fileId)
    // Clear once the flash animation has had time to play - keeping it set
    // forever would re-trigger the scroll/flash on every re-render.
    setTimeout(() => setHighlightedFileId(null), 2000)
  }

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Files"
        actions={
          <>
            <SearchBox folderId={folderId} onHighlightFile={handleHighlightFile} />
            <AddContentMenu folderId={folderId} />
          </>
        }
      />
      <PageBody>
        <FileDataTable folderId={folderId} highlightedFileId={highlightedFileId} />
      </PageBody>
    </div>
  )
}
