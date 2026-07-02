import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function AgentsPage() {
  return (
    <AppShell>
      <PageHeader title="Agent Builder" description="Kavitha's current Rubicorn Technologies development-call behavior." />
      <FeaturePage title="Agent Builder" description="The call flow is configured in code now. Visual editing is under testing and development." status="Beta">
        <div className="grid gap-3 text-sm">
          <InfoRow label="Greeting" value="Kavitha from Rubicorn Technologies" />
          <InfoRow label="Speaks" value="Pure Telugu" />
          <InfoRow label="Collects" value="Need, project type, name, phone number, budget, timeline, and agreement state" />
          <InfoRow label="Unknown question" value="Apologizes and says the team will get back with details" />
          <InfoRow label="If agreed" value="Confirms that the Rubicorn Technologies team will contact them back" />
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
