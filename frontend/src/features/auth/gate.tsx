"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Skeleton } from "@/components/page-kit";
import { useAuth } from "./provider";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const next = encodeURIComponent(
    pathname + (typeof window === "undefined" ? "" : window.location.search),
  );
  if (loading) return <Skeleton />;
  if (!user)
    return (
      <div className="empty">
        <h2>Entre para contribuir.</h2>
        <p>Seu painel e seus rascunhos ficam protegidos pela sua conta.</p>
        <Link className="button" href={`/entrar?next=${next}`}>
          Entrar
        </Link>{" "}
        <Link href={`/cadastro?next=${next}`}>Criar conta</Link>
      </div>
    );
  return children;
}
