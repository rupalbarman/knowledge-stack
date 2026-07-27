import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { authenticationSession } from '@/lib/authentication-session'

export function RequireAuth({ children }: { children: ReactNode }) {
  if (!authenticationSession.isLoggedIn()) {
    return <Navigate to="/sign-in" replace />
  }

  return <>{children}</>
}
