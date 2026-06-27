import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getCalls, recordingUrl } from "@/lib/calls";

export const dynamic = "force-dynamic";

export default async function CallsPage() {
  const calls = await getCalls();

  return (
    <AppShell>
      <PageHeader title="Calls" description="All real caller records with transcript, agreement state, and recording access." showRefresh />
      <div className="p-4 md:p-6">
        <Card>
          <CardHeader>
            <CardTitle>Call Records</CardTitle>
            <CardDescription>Open any caller to review the chat-style conversation and listen to the recording.</CardDescription>
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
                      No calls stored yet. Call the connected Twilio line to create the first real record.
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
      </div>
    </AppShell>
  );
}
