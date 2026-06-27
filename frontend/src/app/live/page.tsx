import { AppShell } from "@/components/app-shell";
import { LiveCallsPanel } from "@/components/call-data-panels";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function LiveCallsPage() {
  return (
    <AppShell>
      <PageHeader title="Live Calls" description="Calls currently being collected by Rubi." showRefresh />
      <FeaturePage title="Live Calls" description="Live call state is visible from stored call status. Real-time push updates are under testing and development." status="Beta">
        <LiveCallsPanel />
      </FeaturePage>
    </AppShell>
  );
}
