import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function TelephonyPage() {
  return (
    <AppShell>
      <PageHeader title="Telephony" description="Inbound phone connection and webhook status." />
      <FeaturePage title="Telephony" description="Twilio inbound calling is connected to the Rubi backend webhook." status="Active">
        <div className="grid gap-3 text-sm">
          <InfoRow label="Contact no" value="+91 76720 10211" />
          <InfoRow label="Inbound provider" value="Twilio" />
          <InfoRow label="Webhook" value="/api/v1/twilio/voice" />
          <InfoRow label="Recording" value="Enabled after call completion when Twilio posts recording data" />
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
