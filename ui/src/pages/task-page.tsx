import { PageBody } from '@/components/page-body'
import { PageHeader } from '@/components/page-header'
import { TaskDataTable } from '@/components/task-data-table'

export function TaskPage() {
  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Tasks" />
      <PageBody>
        <TaskDataTable />
      </PageBody>
    </div>
  )
}
