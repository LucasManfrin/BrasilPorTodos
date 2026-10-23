import { SharedIdea } from "@/features/ideas/public";
export default async function Page({ params }: { params: Promise<{id:string}> }) { const {id} = await params; return <main id="conteudo" tabIndex={-1} className="internal-page"><SharedIdea id={id} /></main>; }
