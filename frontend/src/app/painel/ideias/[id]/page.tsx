import { IdeaEditor } from "@/features/ideas/editor";
export default async function Page({ params, searchParams }: { params: Promise<{id:string}>; searchParams: Promise<Record<string,string|string[]|undefined>> }) {
 const [{id},query] = await Promise.all([params,searchParams]);
 return <IdeaEditor id={id} initialMode={query.modo === "guiado" ? "guided" : "manual"} />;
}
