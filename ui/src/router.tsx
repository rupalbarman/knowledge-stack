import {
  createBrowserRouter,
  RouterProvider,
  useOutletContext,
} from "react-router-dom";

import { RequireAuth } from "@/guards/require-auth";
import { AppLayout, type AppLayoutContext } from "@/layouts/app-layout";
import { AuthenticatePage } from "@/pages/authenticate-page";
import { FilePage } from "@/pages/file-page";
import { HomePage } from "@/pages/home-page";
import { SignInPage } from "@/pages/sign-in-page";
import { SignUpPage } from "@/pages/sign-up-page";
import { TaskPage } from "@/pages/task-page";

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
  {
    path: "/sign-up",
    element: <SignUpPage />,
  },
  {
    path: "/",
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <HomePage /> },
      { path: "files", element: <FilesRoute /> },
      { path: "tasks", element: <TaskPage /> },
    ],
  },
];

const browserRouter = createBrowserRouter(routes);

export const AppRouter = () => <RouterProvider router={browserRouter} />;
