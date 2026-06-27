import { AppShell } from "@/components/app-shell";
import { AnalyticsPanel } from "@/components/call-data-panels";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function AnalyticsPage() {
  return (
    <AppShell>
      <PageHeader title="Analytics" description="Call volume, agreement, and recording metrics." />
      <FeaturePage title="Analytics" description="Basic metrics are available now. Charts and advanced filters are under testing and development." status="Beta">
        <AnalyticsPanel />
      </FeaturePage>
    </AppShell>
  );
}
