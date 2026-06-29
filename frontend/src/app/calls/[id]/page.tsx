import { ArrowLeft, Headphones, Phone } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiPath, isApiConfigured } from "@/lib/api";

export const dynamic = "force-dynamic";

type TranscriptTurn = {
  role: string;
  text: string;
  language: string;
  created_at: string;
};

type StoredCall = {
  id: string;
  provider: string;
  provider_call_id: string;
  from_number: string;
  to_number: string;
  status: string;
  language: string;
  recording_status: string;
  recording_url: string | null;
  recording_sid: string | null;
  lead: {
    name: string | null;
    phone: string | null;
    need: string | null;
    project_type: string | null;
    budget: string | null;
    timeline: string | null;
    preferred_language: string | null;
    callback_notes: string | null;
    language: string;
    agreed: boolean | null;
    status: string;
  };
  transcript: TranscriptTurn[];
  summary: string;
  created_at: string;
  updated_at: string;
};

async function getCall(id: string): Promise<StoredCall | null> {
  if (!isApiConfigured()) {
    return null;
  }
  try {
    const response = await fetch(apiPath(`/api/v1/calls/${id}`), { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return response.json();
  } catch {
    return null;
  }
}

export default async function CallDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const call = await getCall(id);

  if (!call) {
    return (
      <main className="min-h-screen bg-background p-6 text-foreground">
        <Link className="mb-6 inline-flex items-center gap-2 text-sm text-primary" href="/">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <Card>
          <CardHeader>
            <CardTitle>Call Not Found</CardTitle>
            <CardDescription>This call record is not available in local storage.</CardDescription>
          </CardHeader>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background p-4 text-foreground md:p-6">
      <div className="mx-auto grid max-w-6xl gap-6">
        <header className="flex flex-col gap-3 border-b border-border pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <Link className="mb-3 inline-flex items-center gap-2 text-sm text-primary" href="/">
              <ArrowLeft className="h-4 w-4" />
              Dashboard
            </Link>
            <h1 className="text-xl font-semibold tracking-normal">{call.from_number}</h1>
            <p className="text-sm text-muted-foreground">
              {call.language} · {call.status} · {new Date(call.created_at).toLocaleString()}
            </p>
          </div>
          <Badge>{call.lead.status}</Badge>
        </header>

        <section className="grid gap-4 xl:grid-cols-[1fr_360px]">
          <Card>
            <CardHeader>
              <CardTitle>Conversation</CardTitle>
              <CardDescription>Readable chat-style record of what was discussed.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3">
              {call.transcript.length === 0 ? (
                <div className="rounded-lg border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
                  No conversation text captured yet.
                </div>
              ) : (
                call.transcript.map((turn) => (
                  <div
                    key={`${turn.created_at}-${turn.role}-${turn.text}`}
                    className={
                      turn.role === "assistant"
                        ? "ms-auto max-w-[82%] rounded-lg bg-primary/15 p-3 text-sm"
                        : "max-w-[82%] rounded-lg bg-card p-3 text-sm text-muted-foreground"
                    }
                  >
                    <div className="mb-1 text-xs font-medium uppercase text-muted-foreground">
                      {turn.role === "assistant" ? "Rubi" : "Caller"} · {turn.language}
                    </div>
                    {turn.text}
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Recording</CardTitle>
                <CardDescription>Listen after Twilio sends the recording URL.</CardDescription>
              </CardHeader>
              <CardContent>
                {call.recording_url ? (
                  <audio className="w-full" controls src={apiPath(`/api/v1/calls/${call.id}/recording`)} />
                ) : (
                  <div className="rounded-md bg-muted/35 p-3 text-sm text-muted-foreground">
                    Recording status: {call.recording_status}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Lead Details</CardTitle>
                <CardDescription>What Rubi collected during the call.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm">
                <InfoRow label="Name" value={call.lead.name ?? "Not captured"} />
                <InfoRow label="Phone" value={call.lead.phone ?? call.from_number} />
                <InfoRow label="Preferred language" value={call.lead.preferred_language ?? call.lead.language} />
                <InfoRow label="Project type" value={call.lead.project_type ?? "Not captured"} />
                <InfoRow label="Need" value={call.lead.need ?? "Not captured"} />
                <InfoRow label="Budget" value={call.lead.budget ?? "Not captured"} />
                <InfoRow label="Timeline" value={call.lead.timeline ?? "Not captured"} />
                <InfoRow label="Callback notes" value={call.lead.callback_notes ?? "Not captured"} />
                <InfoRow label="Agreement" value={agreementText(call.lead.agreed)} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Summary</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">{call.summary}</CardContent>
            </Card>

            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-1">
              <StatusTile icon={Phone} label="Provider Call ID" value={call.provider_call_id} />
              <StatusTile icon={Headphones} label="Recording SID" value={call.recording_sid ?? "Waiting"} />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function agreementText(value: boolean | null) {
  if (value === true) return "Agreed";
  if (value === false) return "Not agreed";
  return "Pending";
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border pb-3 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="max-w-[220px] text-right font-medium">{value}</span>
    </div>
  );
}

function StatusTile({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md bg-accent text-accent-foreground">
        <Icon className="h-4 w-4" />
      </div>
      <div className="text-sm font-medium">{label}</div>
      <div className="mt-1 break-all text-sm text-muted-foreground">{value}</div>
    </div>
  );
}
