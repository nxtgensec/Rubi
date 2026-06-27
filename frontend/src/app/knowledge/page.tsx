import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function KnowledgePage() {
  return (
    <AppShell>
      <PageHeader title="Knowledge Base" description="The website knowledge Rubi uses while talking to callers." />
      <FeaturePage title="Website Knowledge" description="Rubi answers web development questions from this configured knowledge source." status="Active">
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
              <TableCell>Website content and intake rules</TableCell>
              <TableCell>
                <Badge>Editable</Badge>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </FeaturePage>
    </AppShell>
  );
}
