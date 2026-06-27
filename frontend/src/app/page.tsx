import { Bot, Brain, Cable, Languages, Lock, Phone, Radio, Settings, Shield, Users, Wrench } from "lucide-react";
import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatCallTime, recordingUrl, type Call } from "@/lib/calls";

export default function Home() {
  const calls: Call[] = [];
  const latestCall = calls[0];
  const activeCalls = calls.filter((call) => ["collecting", "qualified"].includes(call.status)).length;
  const agreedCalls = calls.filter((call) => call.sentiment === "agreed").length;
  const recordedCalls = calls.filter((call) => call.recording_url).length;

  return (
    <AppShell>
      <PageHeader
        title="Call Intake Dashboard"
        description="Real calls, recordings, readable notes, budget, and agreement status."
        showRefresh
      />

          <div className="grid gap-6 p-4 md:p-6">
            <section id="analytics" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4 scroll-mt-20">
              <MetricCard label="Total calls" value={String(calls.length)} detail="Stored from Twilio calls" />
              <MetricCard label="Active leads" value={String(activeCalls)} detail="Still collecting details" />
              <MetricCard label="Agreed" value={String(agreedCalls)} detail="Caller accepted team callback" />
              <MetricCard label="Recordings" value={String(recordedCalls)} detail="Recording URL received" />
            </section>

            <section id="live" className="grid gap-4 scroll-mt-20 xl:grid-cols-[1.2fr_0.8fr]">
              <Card>
                <CardHeader className="flex-row items-start justify-between gap-4">
                  <div>
                    <CardTitle>Latest Call</CardTitle>
                    <CardDescription>Transcript, summary, agreement state, and recording status.</CardDescription>
                  </div>
                  <Badge className="border-primary/40 text-primary">
                    <Radio className="mr-1 h-3 w-3" />
                    Real data
                  </Badge>
                </CardHeader>
                <CardContent className="grid gap-4">
                  <div className="grid gap-3 rounded-md border border-border bg-muted/30 p-4">
                    <div>
                      <p className="font-medium">{latestCall?.caller ?? "No calls yet"}</p>
                      <p className="text-sm text-muted-foreground">
                        {latestCall
                          ? `${latestCall.language} - ${latestCall.status} - ${latestCall.recording_status}`
                          : "Call the Twilio number to create the first record."}
                      </p>
                    </div>
                    <div className="grid gap-2 text-sm">
                      {(latestCall?.transcript.length ? latestCall.transcript : ["No transcript captured yet."]).map(
                        (line) => (
                          <p key={line} className="rounded-md bg-card p-3 text-muted-foreground">
                            {line}
                          </p>
                        ),
                      )}
                    </div>
                  </div>
                  <div className="grid gap-3 md:grid-cols-3">
                    <StatusTile icon={Phone} label="Status" value={latestCall?.status ?? "Waiting"} />
                    <StatusTile icon={Bot} label="Summary" value={latestCall?.summary ?? "No call summary yet"} />
                    <StatusTile icon={Languages} label="Language" value={latestCall?.language ?? "English / Telugu / Tenglish"} />
                  </div>
                </CardContent>
              </Card>

              <Card id="agents" className="scroll-mt-20">
                <CardHeader>
                  <div className="flex items-center justify-between gap-3">
                    <CardTitle>Agent Builder</CardTitle>
                    <Badge className="border-amber-500/35 bg-amber-500/10 text-amber-700">Beta</Badge>
                  </div>
                  <CardDescription>The current production intake flow. Full visual editing is under testing.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 text-sm">
                  <ConfigRow label="Contact no" value="+91 76720 10211" />
                  <ConfigRow label="Twilio line" value="Connected for inbound calls" />
                  <ConfigRow label="Speaks" value="English, Telugu, Tenglish" />
                  <ConfigRow label="Collects" value="Name, need, budget, agreement" />
                  <ConfigRow label="When agreed" value="Tells caller the team will get back" />
                  <ConfigRow label="Knowledge" value="docs/business_knowledge.md" />
                </CardContent>
              </Card>
            </section>

            <section id="calls" className="grid gap-4 scroll-mt-20 xl:grid-cols-[1fr_360px]">
              <Card>
                <CardHeader>
                  <CardTitle>Calls</CardTitle>
                  <CardDescription>Readable call records with agreement state and recordings.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Caller</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Language</TableHead>
                        <TableHead>Recording</TableHead>
                        <TableHead>Agreement</TableHead>
                        <TableHead>Summary</TableHead>
                        <TableHead>Chat</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {calls.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={7} className="text-muted-foreground">
                            No calls stored yet. Call the Twilio number to create the first real record.
                          </TableCell>
                        </TableRow>
                      ) : (
                        calls.map((call) => (
                          <TableRow key={call.id}>
                            <TableCell className="font-mono">{call.caller}</TableCell>
                            <TableCell>
                              <Badge>{call.status}</Badge>
                            </TableCell>
                            <TableCell>{call.language}</TableCell>
                            <TableCell>
                              {call.recording_url ? (
                                <a className="text-primary" href={recordingUrl(call.id)}>
                                  Listen
                                </a>
                              ) : (
                                <Badge>{call.recording_status}</Badge>
                              )}
                            </TableCell>
                            <TableCell>{call.sentiment}</TableCell>
                            <TableCell className="max-w-[420px] text-muted-foreground">{call.summary}</TableCell>
                            <TableCell>
                              <Link className="text-primary" href={`/calls/${call.id}`}>
                                Open chat
                              </Link>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card id="logs" className="scroll-mt-20">
                <CardHeader>
                  <CardTitle>Readable Transcript</CardTitle>
                  <CardDescription>What was conveyed in the latest call.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-2">
                  {(latestCall?.transcript.length ? latestCall.transcript : ["Waiting for first real call."]).map(
                    (event) => (
                      <div key={event} className="rounded-md bg-muted/35 px-3 py-2 font-mono text-xs text-muted-foreground">
                        {event}
                      </div>
                    ),
                  )}
                </CardContent>
              </Card>
            </section>

            <section id="history" className="scroll-mt-20">
              <Card>
                <CardHeader>
                  <CardTitle>Call History</CardTitle>
                  <CardDescription>Completed and recent call records, newest first.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Started</TableHead>
                        <TableHead>Caller</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Summary</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {calls.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={4} className="text-muted-foreground">
                            No history yet. Real calls will appear here after Twilio posts them to Rubi.
                          </TableCell>
                        </TableRow>
                      ) : (
                        calls.map((call) => (
                          <TableRow key={call.id}>
                            <TableCell>{formatCallTime(call.started_at)}</TableCell>
                            <TableCell className="font-mono">{call.caller}</TableCell>
                            <TableCell>
                              <Badge>{call.status}</Badge>
                            </TableCell>
                            <TableCell className="max-w-[560px] text-muted-foreground">{call.summary}</TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-4 scroll-mt-20 xl:grid-cols-2">
              <Card id="knowledge" className="scroll-mt-20">
                <CardHeader>
                  <CardTitle>Website Knowledge</CardTitle>
                  <CardDescription>Rubi answers from this local business knowledge file.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Source</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>docs/business_knowledge.md</TableCell>
                        <TableCell>Website content</TableCell>
                        <TableCell>
                          <Badge>Editable</Badge>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card id="voices" className="scroll-mt-20">
                <CardHeader>
                  <div className="flex items-center justify-between gap-3">
                    <CardTitle>Voices And Language</CardTitle>
                    <Badge className="border-amber-500/35 bg-amber-500/10 text-amber-700">Beta</Badge>
                  </div>
                  <CardDescription>English is stable. Telugu and Tenglish are active in the intake flow and still being tuned.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 text-sm">
                  <ConfigRow label="English" value="Twilio speech and voice" />
                  <ConfigRow label="Telugu" value="Detected from Telugu/Tenglish text cues" />
                  <ConfigRow label="Tenglish" value="Supported for intake prompts" />
                  <ConfigRow label="Call data" value="data/rubi_store.json" />
                  <ConfigRow label="Recordings" value="Twilio recording URL" />
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <StatusTile id="telephony" icon={Cable} label="Telephony" value="Inbound webhook answers calls" />
              <StatusTile id="tools" icon={Wrench} label="Tools" value="Beta: recording, transcript, lead intake tools are connected" badge="Beta" />
              <StatusTile id="models" icon={Brain} label="Models" value="Beta: structured intake logic, no full LLM handoff yet" badge="Beta" />
              <StatusTile icon={Bot} label="Lead State" value="Agreed / not agreed / collecting" />
            </section>

            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <FeaturePanel
                id="settings"
                icon={Settings}
                title="Settings"
                status="Beta"
                description="Webhook URL, storage mode, Twilio number, and Supabase connection are configured through environment files for now."
              />
              <FeaturePanel
                id="users"
                icon={Users}
                title="Users"
                status="Beta"
                description="Single admin dashboard is available. Multi-user login and roles are under testing and development."
              />
              <FeaturePanel
                id="security"
                icon={Shield}
                title="Security"
                status="Beta"
                description="Secrets stay server-side and local files are ignored by git. Full dashboard authentication is still under development."
              />
              <FeaturePanel
                icon={Lock}
                title="Safe Storage"
                status="Active"
                description="Call notes, transcripts, agreement state, and recording links are stored by the backend for review."
              />
            </section>
          </div>
    </AppShell>
  );
}

function MetricCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  );
}

function StatusTile({
  id,
  icon: Icon,
  label,
  value,
  badge,
}: {
  id?: string;
  icon: React.ElementType;
  label: string;
  value: string;
  badge?: string;
}) {
  return (
    <div id={id} className="scroll-mt-20 rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md bg-accent text-accent-foreground">
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex items-center justify-between gap-2">
        <div className="text-sm font-medium">{label}</div>
        {badge ? <Badge className="border-amber-500/35 bg-amber-500/10 text-amber-700">{badge}</Badge> : null}
      </div>
      <div className="mt-1 text-sm text-muted-foreground">{value}</div>
    </div>
  );
}

function FeaturePanel({
  id,
  icon: Icon,
  title,
  status,
  description,
}: {
  id?: string;
  icon: React.ElementType;
  title: string;
  status: string;
  description: string;
}) {
  return (
    <Card id={id} className="scroll-mt-20">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-accent-foreground">
              <Icon className="h-4 w-4" />
            </div>
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <Badge className={status === "Active" ? "border-primary/40 text-primary" : "border-amber-500/35 bg-amber-500/10 text-amber-700"}>
            {status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function ConfigRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border pb-3 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
