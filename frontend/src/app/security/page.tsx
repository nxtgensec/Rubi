import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function SecurityPage() {
  return (
    <AppShell>
      <PageHeader title="Security" description="Security and access-control readiness." />
      <FeaturePage title="Security" description="Server-side secrets are separated. Full dashboard authentication is under testing and development." status="Beta">
        <div className="grid gap-3 text-sm">
          <InfoRow label="Secrets" value="Kept server-side and ignored from git" />
          <InfoRow label="Recording access" value="Proxied through backend recording endpoint" />
          <InfoRow label="Dashboard login" value="Under testing and development" />
          <InfoRow label="Role permissions" value="Under testing and development" />
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
