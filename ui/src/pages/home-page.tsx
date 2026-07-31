import { AnalyticsBar } from '@/components/analytics-bar'
import { PageBody } from '@/components/page-body'
import { PageHeader } from '@/components/page-header'

export function HomePage() {
  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Home" />
      <PageBody>
        <div className="flex flex-col gap-6">
          <AnalyticsBar />
        </div>
      </PageBody>
    </div>
  )
}
