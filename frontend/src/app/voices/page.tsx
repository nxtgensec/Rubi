import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function VoicesPage() {
  return (
    <AppShell>
      <PageHeader title="Voices" description="Language and voice behavior for calls." />
      <FeaturePage title="Voices And Language" description="English is stable. Telugu and Tenglish prompts are active and still being tuned." status="Beta">
        <div className="grid gap-3 text-sm">
          <InfoRow label="English" value="Twilio speech and voice" />
          <InfoRow label="Telugu" value="Supported through Telugu/Tenglish call prompts" />
          <InfoRow label="Tenglish" value="Supported for intake and fallback prompts" />
          <InfoRow label="Natural Telugu voice" value="Under testing and development" />
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
