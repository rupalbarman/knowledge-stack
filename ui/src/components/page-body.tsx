import type { ReactNode } from 'react'

export function PageBody({ children }: { children: ReactNode }) {
  return <div className="flex-1 overflow-auto p-6">{children}</div>
}
