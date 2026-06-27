import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatCallTime, getCalls } from "@/lib/calls";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  const calls = await getCalls();

  return (
    <AppShell>
      <PageHeader title="Call History" description="Chronological call history, newest first." showRefresh />
      <div className="p-4 md:p-6">
        <Card>
          <CardHeader>
            <CardTitle>History</CardTitle>
            <CardDescription>Past and recent call outcomes stored by Rubi.</CardDescription>
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
                      No call history yet.
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
      </div>
    </AppShell>
  );
}
