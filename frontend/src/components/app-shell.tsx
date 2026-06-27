"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { navigation } from "@/data/navigation";
import { cn } from "@/lib/utils";

const primaryMobileLabels = new Set(["Dashboard", "Calls", "Call History", "Analytics", "Telephony"]);

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const primaryMobileNav = navigation.filter((item) => primaryMobileLabels.has(item.label));
  const secondaryMobileNav = navigation.filter((item) => !primaryMobileLabels.has(item.label));

  return (
    <main className="min-h-screen bg-background pb-20 text-foreground lg:pb-0">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[260px] overflow-y-auto border-r border-border bg-card/95 backdrop-blur lg:block">
          <div className="flex h-16 items-center border-b border-border px-5">
            <div>
              <div className="text-lg font-semibold">Rubi</div>
              <div className="text-xs text-muted-foreground">AI Voice Employee</div>
            </div>
          </div>
          <nav className="grid gap-1 p-3">
            {navigation.map((item) => {
              const active = item.href === "/" ? pathname === item.href : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={cn(
                    "flex h-9 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    active && "bg-accent text-accent-foreground",
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="min-w-0 flex-1">{item.label}</span>
                  {item.status === "beta" ? (
                    <span className="rounded border border-amber-500/35 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium uppercase text-amber-700">
                      Beta
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </nav>
      </aside>

      <div className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur lg:hidden">
        <div className="flex h-14 items-center justify-between px-4">
          <div>
            <div className="text-base font-semibold">Rubi</div>
            <div className="text-xs text-muted-foreground">AI Voice Employee</div>
          </div>
          <button
            type="button"
            aria-expanded={mobileMenuOpen}
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            className="flex h-10 w-10 items-center justify-center rounded-md border border-border bg-background text-foreground"
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        {mobileMenuOpen ? (
          <nav className="mobile-menu-scroll grid max-h-[65vh] gap-1 overflow-y-auto border-t border-border p-3">
            {secondaryMobileNav.map((item) => {
              const active = item.href === "/" ? pathname === item.href : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex h-11 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground",
                    active && "bg-accent text-accent-foreground",
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="min-w-0 flex-1">{item.label}</span>
                  {item.status === "beta" ? (
                    <span className="rounded border border-amber-500/35 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium uppercase text-amber-700">
                      Beta
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </nav>
        ) : null}
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-40 grid h-16 grid-cols-5 border-t border-border bg-card/95 px-1 pb-[env(safe-area-inset-bottom)] shadow-2xl backdrop-blur lg:hidden">
        {primaryMobileNav.map((item) => {
            const active = item.href === "/" ? pathname === item.href : pathname.startsWith(item.href);
            return (
              <Link
                key={item.label}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  "flex min-w-0 flex-col items-center justify-center gap-1 rounded-md px-1 text-[11px] font-medium text-muted-foreground",
                  active && "text-primary",
                )}
              >
                <item.icon className="h-4 w-4" />
                <span className="max-w-full truncate">{item.label === "Call History" ? "History" : item.label}</span>
              </Link>
            );
        })}
      </nav>

      <section className="min-w-0 lg:pl-[260px]">{children}</section>
    </main>
  );
}
