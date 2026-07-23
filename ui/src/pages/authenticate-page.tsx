import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { authenticationSession } from '@/lib/authentication-session'

// Entry point for the "managed" embedding mode: the host application signs
// the user in elsewhere and redirects here with a token, skipping our own
// sign-in/sign-up flow entirely.
export function AuthenticatePage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setError('Missing token')
      return
    }
    authenticationSession.saveToken(token)
    navigate('/', { replace: true })
  }, [searchParams, navigate])

  return (
    <div className="bg-background text-foreground flex min-h-screen items-center justify-center">
      <p className={error ? 'text-destructive text-sm' : 'text-sm'}>
        {error ?? 'Authenticating...'}
      </p>
    </div>
  )
}
