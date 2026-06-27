import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function SettingsPage() {
  return (
    <AppShell>
      <PageHeader title="Settings" description="Configuration status for Rubi." />
      <FeaturePage title="Settings" description="Configuration is environment-based right now. In-app editing is under testing and development." status="Beta">
        <div className="grid gap-3 text-sm">
          <InfoRow label="Backend API" value="Configured by NEXT_PUBLIC_API_URL" />
          <InfoRow label="Storage" value="Backend storage service, with Supabase visitor tracking connected" />
          <InfoRow label="Twilio" value="Configured server-side through environment variables" />
          <InfoRow label="Dashboard editing" value="Under testing and development" />
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
