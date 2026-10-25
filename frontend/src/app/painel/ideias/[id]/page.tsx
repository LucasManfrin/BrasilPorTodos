import { IdeaEditor } from "@/features/ideas/editor";
import { QuickIdea } from "@/features/ideas/quick-idea";
import { ideaScreen } from "@/features/ideas/navigation";

export default async function Page({ params, searchParams }: { params: Promise<{id:string}>; searchParams: Promise<Record<string,string|string[]|undefined>> }) {
 const [{id},query] = await Promise.all([params,searchParams]);
 const screen = ideaScreen(query);
 return screen === "quick" ? <QuickIdea id={id} /> : <IdeaEditor id={id} initialMode={screen} />;
}
