import { PolicyEditor } from "@/features/contribution/policy-editor";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <PolicyEditor id={id} />;
}
