import { AppShell } from "@/components/app-shell";
import { FeaturePage } from "@/components/feature-page";
import { PageHeader } from "@/components/page-header";

export default function UsersPage() {
  return (
    <AppShell>
      <PageHeader title="Users" description="Dashboard access and team roles." />
      <FeaturePage title="Users" description="Single-admin usage is available locally. Multi-user accounts are under testing and development." status="Beta">
        <div className="rounded-md bg-muted/35 p-4 text-sm text-muted-foreground">
          Login, roles, and team member permissions are not fully developed yet.
        </div>
      </FeaturePage>
    </AppShell>
  );
}
