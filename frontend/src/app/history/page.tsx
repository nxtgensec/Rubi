import { AppShell } from "@/components/app-shell";
import { HistoryTablePanel } from "@/components/call-data-panels";
import { PageHeader } from "@/components/page-header";

export default function HistoryPage() {
  return (
    <AppShell>
      <PageHeader title="Call History" description="Chronological call history, newest first." showRefresh />
      <div className="p-4 md:p-6">
        <HistoryTablePanel />
      </div>
    </AppShell>
  );
}
