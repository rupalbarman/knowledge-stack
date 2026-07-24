import {
  Suspense,
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import {
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  User,
  Home,
} from "lucide-react";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { userHooks } from "@/hooks/user-hooks";
import { authenticationSession } from "@/lib/authentication-session";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";

export type SidebarMode = "full" | "small";

type SidebarProps = {
  children?: ReactNode;
};

type SidebarModeContextValue = {
  mode: SidebarMode;
  setMode: (mode: SidebarMode) => void;
};

const SidebarModeContext = createContext<SidebarModeContextValue>({
  mode: "full",
  setMode: () => {},
});

export function useSidebarMode() {
  return useContext(SidebarModeContext);
}

// Icon + label in "full" mode, icon-only (label moves to a hover tooltip) in
// "small" mode. Set iconOnly for buttons that don't have a distinct full-view
// treatment - e.g. the collapse/expand toggle itself - so they stay icon-only
// even in "full" mode.
// todo: iconOnly buttons only get a hover tooltip in "small" mode - in "full"
// mode they show no label and no tooltip. Fine for now (the icon reads on its
// own), but worth wrapping in Tooltip regardless of mode if that changes.
export function SidebarButton({
  icon,
  label,
  onClick,
  iconOnly = false,
}: {
  icon: ReactNode;
  label: string;
  onClick: () => void;
  iconOnly?: boolean;
}) {
  const { mode } = useSidebarMode();

  const button = (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "hover:bg-accent text-foreground flex items-center gap-2 rounded-md px-2 py-2 text-sm",
        mode !== "full" && "justify-center",
        !iconOnly && "w-full",
      )}
    >
      {icon}
      {!iconOnly && mode === "full" && (
        <span className="truncate">{label}</span>
      )}
    </button>
  );

  if (mode === "full") {
    return button;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent side="right">{label}</TooltipContent>
    </Tooltip>
  );
}

// Split out (and Suspense-wrapped here, not by the caller) since
// userHooks.useCurrentUser uses useSuspenseQuery - keeping that requirement
// contained means Sidebar itself stays a plain drop-in component.
function SidebarUserFooter() {
  const { data: user } = userHooks.useCurrentUser();

  return (
    <div className="border-border space-y-1 border-t p-2">
      <SidebarButton
        icon={<User className="size-4 shrink-0" />}
        label={user?.email ?? "Account"}
        // No profile page/menu yet - wire up once there's somewhere to go.
        onClick={() => {}}
      />
      <SidebarButton
        icon={<LogOut className="size-4 shrink-0" />}
        label="Log out"
        onClick={() => authenticationSession.logOut()}
      />
    </div>
  );
}

function SidebarHeader() {
  const { mode, setMode } = useSidebarMode();
  const navigate = useNavigate();
  return (
    <div
      className={cn(
        "border-border flex border-b p-2",
        mode === "full" ? "h-14 items-center justify-end" : "flex-col gap-1",
      )}
    >
      <SidebarButton
        icon={<Home className="size-4 shrink-0" />}
        label="Home"
        onClick={() => navigate("/")}
      />
      <SidebarButton
        icon={
          mode === "full" ? (
            <PanelLeftClose className="size-4 shrink-0" />
          ) : (
            <PanelLeftOpen className="size-4 shrink-0" />
          )
        }
        label={mode === "full" ? "Collapse" : "Expand"}
        onClick={() => setMode(mode === "full" ? "small" : "full")}
        iconOnly
      />
    </div>
  );
}

function SidebarBody({ children }: { children: ReactNode }) {
  return <nav className="flex-1 space-y-4 overflow-y-auto p-2">{children}</nav>;
}

// Groups related sidebar body content under a labeled "widget" (e.g.
// "Folders"). Hides itself entirely in "small" mode - a folder tree (or any
// other non-trivial content a section might hold) has no sensible collapsed
// form, unlike a plain SidebarButton. The gap between sections is handled by
// SidebarBody's space-y-4, not by this component.
export function SidebarSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  const { mode } = useSidebarMode();

  if (mode !== "full") {
    return null;
  }

  return (
    <div className="space-y-1">
      <p className="text-muted-foreground px-2 text-xs font-medium tracking-wide uppercase">
        {title}
      </p>
      {children}
    </div>
  );
}

export function Sidebar({ children }: SidebarProps) {
  const [mode, setMode] = useState<SidebarMode>("full");

  return (
    <SidebarModeContext.Provider value={{ mode, setMode }}>
      <aside
        className={cn(
          "bg-card border-border flex h-screen flex-col border-r transition-[width] duration-150",
          mode === "full" ? "w-60" : "w-16",
        )}
      >
        <SidebarHeader />

        <SidebarBody>{children}</SidebarBody>

        <Suspense fallback={<div className="border-border border-t p-2" />}>
          <SidebarUserFooter />
        </Suspense>
      </aside>
    </SidebarModeContext.Provider>
  );
}
