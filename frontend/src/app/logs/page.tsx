import { AppShell } from "@/components/app-shell";
import { LatestTranscriptPanel } from "@/components/call-data-panels";
import { PageHeader } from "@/components/page-header";

export default function LogsPage() {
  return (
    <AppShell>
      <PageHeader title="Logs" description="Readable transcript lines captured from the latest call." showRefresh />
      <div className="p-4 md:p-6">
        <LatestTranscriptPanel />
      </div>
    </AppShell>
  );
}
