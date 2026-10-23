import { ContextEditor } from "@/features/contexts/context-editor";
export default async function Page({ searchParams }: {
    searchParams: Promise<{
        indicador?: string;
    }>;
}) { const { indicador } = await searchParams; return <ContextEditor initialIndicatorCode={indicador}/>; }
