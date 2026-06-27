import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function FeaturePage({
  title,
  description,
  status,
  children,
}: {
  title: string;
  description: string;
  status?: "Active" | "Beta";
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-4 p-4 md:p-6">
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          {status ? (
            <Badge className={status === "Active" ? "border-primary/40 text-primary" : "border-amber-500/35 bg-amber-500/10 text-amber-700"}>
              {status}
            </Badge>
          ) : null}
        </CardHeader>
        <CardContent>{children}</CardContent>
      </Card>
    </div>
  );
}
