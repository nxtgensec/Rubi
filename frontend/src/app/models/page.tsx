import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function ModelsPage() {
  return (
    <AppShell>
      <PageHeader title="Models" description="AI and decision logic status." />
      <FeaturePage title="Models" description="Rubi currently uses a structured intake flow. Full LLM model switching is under testing and development." status="Beta">
        <div className="grid gap-3 text-sm">
          <InfoRow label="Current mode" value="Structured web development intake agent" />
          <InfoRow label="Knowledge source" value="docs/business_knowledge.md" />
          <InfoRow label="Unknown questions" value="Fallback to team callback message" />
          <InfoRow label="Model picker" value="Under testing and development" />
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
