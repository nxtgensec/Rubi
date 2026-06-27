import { AppShell } from "@/components/app-shell";
import { CallsTablePanel } from "@/components/call-data-panels";
import { PageHeader } from "@/components/page-header";

export default function CallsPage() {
  return (
    <AppShell>
      <PageHeader title="Calls" description="All real caller records with transcript, agreement state, and recording access." showRefresh />
      <div className="p-4 md:p-6">
        <CallsTablePanel />
      </div>
    </AppShell>
  );
}
