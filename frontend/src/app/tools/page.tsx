import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function ToolsPage() {
  return (
    <AppShell>
      <PageHeader title="Tools" description="Operational tools available to Rubi." />
      <FeaturePage title="Tools" description="Core call tools are connected. Manual admin actions are under testing and development." status="Beta">
        <div className="grid gap-3 text-sm">
          <InfoRow label="Recording playback" value="Available from call records after Twilio sends recording URL" />
          <InfoRow label="Transcript viewer" value="Available from each caller chat page" />
          <InfoRow label="Lead intake" value="Name, phone, requirement, budget, and agreement status" />
          <InfoRow label="Manual edits" value="Under testing and development" />
        </div>
      </FeaturePage>
    </AppShell>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border pb-3 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="max-w-[520px] text-right font-medium">{value}</span>
    </div>
  );
}
