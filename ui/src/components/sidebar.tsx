import { Suspense, useState, type ReactNode } from "react";
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

// todo: iconOnly buttons only get a hover tooltip in "small" mode - in "full"
// mode they show no label and no tooltip. Fine for now (the icon reads on its
// own), but worth wrapping in Tooltip regardless of mode if that changes.
function SidebarButton({
  icon,
  label,
  onClick,
  mode,
  iconOnly = false,
}: {
  icon: ReactNode;
  label: string;
  onClick: () => void;
  mode: SidebarMode;
  iconOnly?: boolean;
}) {
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
function SidebarUserFooter({ mode }: { mode: SidebarMode }) {
  const { data: user } = userHooks.useCurrentUser();

  return (
    <div className="border-border space-y-1 border-t p-2">
      <SidebarButton
        icon={<User className="size-4 shrink-0" />}
        label={user?.email ?? "Account"}
        // No profile page/menu yet - wire up once there's somewhere to go.
        onClick={() => {}}
        mode={mode}
      />
      <SidebarButton
        icon={<LogOut className="size-4 shrink-0" />}
        label="Log out"
        onClick={() => authenticationSession.logOut()}
        mode={mode}
      />
    </div>
  );
}

function SidebarHeader({
  mode,
  setMode,
}: {
  mode: SidebarMode;
  setMode: (mode: SidebarMode) => void;
}) {
  const navigate = useNavigate();
  return (
    <div
      className={cn(
        "border-border flex border-b p-2",
        mode === "full"
          ? "h-14 items-center justify-end"
          : "flex-col gap-1",
      )}
    >
      <SidebarButton
        icon={<Home className="size-4 shrink-0" />}
        label="Home"
        onClick={() => navigate("/")}
        mode={mode}
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
        mode={mode}
        iconOnly
      />
    </div>
  );
}

function SidebarBody({
  mode,
  children,
}: {
  mode: SidebarMode;
  children: ReactNode;
}) {
  return (
    <nav className="flex-1 overflow-y-auto p-2">
      {mode === "full" && children}
    </nav>
  );
}

export function Sidebar({ children }: SidebarProps) {
  const [mode, setMode] = useState<SidebarMode>("full");

  return (
    <aside
      className={cn(
        "bg-card border-border flex h-screen flex-col border-r transition-[width] duration-150",
        mode === "full" ? "w-60" : "w-16",
      )}
    >
      <SidebarHeader mode={mode} setMode={setMode} />

      <SidebarBody mode={mode} children={children} />

      <Suspense fallback={<div className="border-border border-t p-2" />}>
        <SidebarUserFooter mode={mode} />
      </Suspense>
    </aside>
  );
}
