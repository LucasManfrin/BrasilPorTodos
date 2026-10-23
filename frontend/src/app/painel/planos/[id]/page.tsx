import { PlanEditor } from "@/features/contribution/plan-editor";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <PlanEditor id={id} />;
}
