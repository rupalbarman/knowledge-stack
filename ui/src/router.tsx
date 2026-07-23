import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import App from '@/app'
import { RequireAuth } from '@/guards/require-auth'
import { AuthenticatePage } from '@/pages/authenticate-page'
import { SignInPage } from '@/pages/sign-in-page'

const routes = [
  {
    path: '/authenticate',
    element: <AuthenticatePage />,
  },
  {
    path: '/sign-in',
    element: <SignInPage />,
  },
  {
    path: '/',
    element: (
      <RequireAuth>
        <App />
      </RequireAuth>
    ),
  },
]

const browserRouter = createBrowserRouter(routes)

export const AppRouter = () => <RouterProvider router={browserRouter} />
