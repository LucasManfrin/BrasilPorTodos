import { ContextEditor } from "@/features/contexts/context-editor";
export default async function Page({ params }: {
    params: Promise<{
        id: string;
    }>;
}) { const { id } = await params; return <ContextEditor id={id}/>; }
