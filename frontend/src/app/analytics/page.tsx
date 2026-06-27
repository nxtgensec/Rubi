import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCalls } from "@/lib/calls";

export const dynamic = "force-dynamic";

export default async function AnalyticsPage() {
  const calls = await getCalls();
  const agreedCalls = calls.filter((call) => call.sentiment === "agreed").length;
  const recordedCalls = calls.filter((call) => call.recording_url).length;

  return (
    <AppShell>
      <PageHeader title="Analytics" description="Call volume, agreement, and recording metrics." />
      <FeaturePage title="Analytics" description="Basic metrics are available now. Charts and advanced filters are under testing and development." status="Beta">
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Total calls" value={String(calls.length)} />
          <MetricCard label="Agreed" value={String(agreedCalls)} />
          <MetricCard label="Recordings" value={String(recordedCalls)} />
        </div>
      </FeaturePage>
    </AppShell>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">Live from stored call records.</CardContent>
    </Card>
  );
}
