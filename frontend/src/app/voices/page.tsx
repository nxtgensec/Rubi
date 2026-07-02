import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function VoicesPage() {
  return (
    <AppShell>
      <PageHeader title="Voices" description="Language and voice behavior for calls." />
      <FeaturePage title="Voices And Language" description="Sarvam Telugu voice is active for Kavitha's Rubicorn Technologies phone prompts. Twilio still handles call routing and speech capture." status="Beta">
        <div className="grid gap-3 text-sm">
          <InfoRow label="Primary language" value="Pure Telugu" />
          <InfoRow label="Voice provider" value="Sarvam Bulbul Telugu voice" />
          <InfoRow label="Speech capture" value="Twilio Gather with Telugu recognition" />
          <InfoRow label="Voice style" value="Polite, pleasant Telugu woman voice" />
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
