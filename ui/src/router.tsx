import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import { RequireAuth } from '@/guards/require-auth'
import { AuthenticatePage } from '@/pages/authenticate-page'
import { HomePage } from '@/pages/home-page'
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
        <HomePage />
      </RequireAuth>
    ),
  },
]

const browserRouter = createBrowserRouter(routes)

export const AppRouter = () => <RouterProvider router={browserRouter} />
