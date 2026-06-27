import { Radio } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { getCalls } from "@/lib/calls";

export const dynamic = "force-dynamic";

export default async function LiveCallsPage() {
  const calls = await getCalls();
  const activeCalls = calls.filter((call) => ["collecting", "qualified"].includes(call.status));

  return (
    <AppShell>
      <PageHeader title="Live Calls" description="Calls currently being collected by Rubi." showRefresh />
      <FeaturePage title="Live Calls" description="Live call state is visible from stored call status. Real-time push updates are under testing and development." status="Beta">
        <div className="grid gap-3">
          {activeCalls.length === 0 ? (
            <div className="rounded-md bg-muted/35 p-4 text-sm text-muted-foreground">No active calls right now.</div>
          ) : (
            activeCalls.map((call) => (
              <div key={call.id} className="flex items-center justify-between gap-4 rounded-md border border-border p-4">
                <div>
                  <div className="font-mono text-sm">{call.caller}</div>
                  <div className="text-sm text-muted-foreground">{call.summary}</div>
                </div>
                <Badge className="border-primary/40 text-primary">
                  <Radio className="mr-1 h-3 w-3" />
                  {call.status}
                </Badge>
              </div>
            ))
          )}
        </div>
      </FeaturePage>
    </AppShell>
  );
}
