import { AddContentMenu } from '@/components/add-content-menu'
import { FileDataTable } from '@/components/file-data-table'
import { PageBody } from '@/components/page-body'
import { PageHeader } from '@/components/page-header'

type FilePageProps = {
  folderId: string | null
}

export function FilePage({ folderId }: FilePageProps) {
  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Files"
        actions={<AddContentMenu folderId={folderId} />}
      />
      <PageBody>
        <FileDataTable folderId={folderId} />
      </PageBody>
    </div>
  )
}
