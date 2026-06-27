import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCalls } from "@/lib/calls";

export const dynamic = "force-dynamic";

export default async function LogsPage() {
  const calls = await getCalls();
  const latestCall = calls[0];

  return (
    <AppShell>
      <PageHeader title="Logs" description="Readable transcript lines captured from the latest call." showRefresh />
      <div className="p-4 md:p-6">
        <Card>
          <CardHeader>
            <CardTitle>Latest Transcript</CardTitle>
            <CardDescription>What was conveyed in the call.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            {(latestCall?.transcript.length ? latestCall.transcript : ["Waiting for first real call."]).map((event) => (
              <div key={event} className="rounded-md bg-muted/35 px-3 py-2 font-mono text-xs text-muted-foreground">
                {event}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
