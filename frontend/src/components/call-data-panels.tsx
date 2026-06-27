"use client";

import { Radio } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiPath } from "@/lib/api";
import { formatCallTime, recordingUrl, type Call } from "@/lib/calls";

type CallsState = {
  calls: Call[];
  loading: boolean;
  error: string | null;
};

function useCalls(): CallsState {
  const [state, setState] = useState<CallsState>({ calls: [], loading: true, error: null });

  useEffect(() => {
    let active = true;

    async function loadCalls() {
      try {
        const response = await fetch(apiPath("/api/v1/calls"), { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }
        const calls = (await response.json()) as Call[];
        if (active) {
          setState({ calls, loading: false, error: null });
        }
      } catch {
        if (active) {
          setState({ calls: [], loading: false, error: "Could not load call records right now." });
        }
      }
    }

    loadCalls();
    const interval = window.setInterval(loadCalls, 15000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return state;
}

function DataStatus({ loading, error, empty }: { loading: boolean; error: string | null; empty: string }) {
  if (loading) {
    return <span className="text-muted-foreground">Loading live records...</span>;
  }
  if (error) {
    return <span className="text-amber-500">{error}</span>;
  }
  return <span className="text-muted-foreground">{empty}</span>;
}

export function CallsTablePanel() {
  const { calls, loading, error } = useCalls();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Call Records</CardTitle>
        <CardDescription>Open any caller to review the chat-style conversation and listen to the recording.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
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
                  <TableCell colSpan={7}>
                    <DataStatus
                      loading={loading}
                      error={error}
                      empty="No calls stored yet. Call the connected Twilio line to create the first real record."
                    />
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
        </div>
      </CardContent>
    </Card>
  );
}

export function HistoryTablePanel() {
  const { calls, loading, error } = useCalls();

  return (
    <Card>
      <CardHeader>
        <CardTitle>History</CardTitle>
        <CardDescription>Past and recent call outcomes stored by Rubi.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
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
                  <TableCell colSpan={4}>
                    <DataStatus loading={loading} error={error} empty="No call history yet." />
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
        </div>
      </CardContent>
    </Card>
  );
}

export function AnalyticsPanel() {
  const { calls, loading, error } = useCalls();
  const metrics = useMemo(
    () => ({
      agreed: calls.filter((call) => call.sentiment === "agreed").length,
      recorded: calls.filter((call) => call.recording_url).length,
    }),
    [calls],
  );

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <MetricCard label="Total calls" value={loading ? "..." : String(calls.length)} />
      <MetricCard label="Agreed" value={loading ? "..." : String(metrics.agreed)} />
      <MetricCard label="Recordings" value={loading ? "..." : String(metrics.recorded)} />
      {error ? <div className="text-sm text-amber-500 md:col-span-3">{error}</div> : null}
    </div>
  );
}

export function LiveCallsPanel() {
  const { calls, loading, error } = useCalls();
  const activeCalls = calls.filter((call) => ["collecting", "qualified"].includes(call.status));

  if (activeCalls.length === 0) {
    return (
      <div className="rounded-md bg-muted/35 p-4 text-sm">
        <DataStatus loading={loading} error={error} empty="No active calls right now." />
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {activeCalls.map((call) => (
        <div key={call.id} className="flex items-center justify-between gap-4 rounded-md border border-border p-4">
          <div>
            <div className="font-mono text-sm">{call.caller}</div>
            <div className="text-sm text-muted-foreground">{call.summary}</div>
          </div>
          <Badge className="border-primary/40 text-primary">
            <Radio className="mr-1 h-3 w-3" />
            {call.status}
          </Badge>
        </div>
      ))}
    </div>
  );
}

export function LatestTranscriptPanel() {
  const { calls, loading, error } = useCalls();
  const latestCall = calls[0];
  const lines = latestCall?.transcript.length ? latestCall.transcript : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Latest Transcript</CardTitle>
        <CardDescription>What was conveyed in the call.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2">
        {lines ? (
          lines.map((event) => (
            <div key={event} className="rounded-md bg-muted/35 px-3 py-2 font-mono text-xs text-muted-foreground">
              {event}
            </div>
          ))
        ) : (
          <div className="rounded-md bg-muted/35 px-3 py-2 text-sm">
            <DataStatus loading={loading} error={error} empty="Waiting for first real call." />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">Live from stored call records.</CardContent>
    </Card>
  );
}
