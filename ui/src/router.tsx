import {
  createBrowserRouter,
  RouterProvider,
  useOutletContext,
} from "react-router-dom";

import { RequireAuth } from "@/guards/require-auth";
import { AppLayout, type AppLayoutContext } from "@/layouts/app-layout";
import { AuthenticatePage } from "@/pages/authenticate-page";
import { FilePage } from "@/pages/file-page";
import { SignInPage } from "@/pages/sign-in-page";

function FilesRoute() {
  const { selectedFolderId } = useOutletContext<AppLayoutContext>();
  return <FilePage folderId={selectedFolderId} />;
}

const routes = [
  {
    path: "/authenticate",
    element: <AuthenticatePage />,
  },
  {
    path: "/sign-in",
    element: <SignInPage />,
  },
  // todo(Rupal): move this to a dedicated 'files' route once we have a different 'home' page
  {
    path: "/",
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [{ index: true, element: <FilesRoute /> }],
  },
];

const browserRouter = createBrowserRouter(routes);

export const AppRouter = () => <RouterProvider router={browserRouter} />;
