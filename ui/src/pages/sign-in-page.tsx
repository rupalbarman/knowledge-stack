import { type SubmitEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '@/lib/api'
import { authenticationApi } from '@/lib/authentication-api'
import { authenticationSession } from '@/lib/authentication-session'

export function SignInPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      const response = await authenticationApi.signIn({ email, password })
      authenticationSession.saveResponse(response)
      navigate('/')
    } catch (err) {
      setError(
        api.isError(err) && err.response?.status === api.httpStatus.Unauthorized
          ? 'Invalid email or password'
          : 'Something went wrong, please try again',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="bg-background text-foreground flex min-h-screen items-center justify-center">
      <form
        onSubmit={handleSubmit}
        className="border-border bg-card w-80 space-y-4 rounded-md border p-6"
      >
        <h1 className="text-lg font-semibold">Sign in</h1>

        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="border-border w-full rounded-md border bg-transparent px-3 py-2 text-sm"
        />
        <input
          type="password"
          required
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="border-border w-full rounded-md border bg-transparent px-3 py-2 text-sm"
        />

        {error && <p className="text-destructive text-sm">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="bg-primary text-primary-foreground w-full rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
