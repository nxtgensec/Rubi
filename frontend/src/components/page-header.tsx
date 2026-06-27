import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

export function PageHeader({
  title,
  description,
  showRefresh = false,
}: {
  title: string;
  description: string;
  showRefresh?: boolean;
}) {
  return (
    <header className="sticky top-14 z-20 flex min-h-16 flex-col items-start justify-between gap-3 border-b border-border bg-background/95 px-4 py-3 backdrop-blur md:flex-row md:items-center md:px-6 lg:top-0">
      <div className="min-w-0">
        <h1 className="text-xl font-semibold tracking-normal">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {showRefresh ? (
        <Button variant="secondary">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      ) : null}
    </header>
  );
}
