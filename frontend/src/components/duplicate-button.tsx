"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/features/auth/provider";
import type { Plan, Policy } from "@/lib/types";
import { Icon } from "./ui";
import { fiscalMetadataBody } from "@/lib/fiscal-compatibility";
import { fiscalScenarioBody } from "@/lib/fiscal-scenario";

export function DuplicateButton({
  kind,
  slug,
  versionNumber,
}: {
  kind: "policies" | "plans";
  slug: string;
  versionNumber: number;
}) {
  const { user, loading, request } = useAuth();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function duplicate() {
    setBusy(true);
    setError("");
    const path = kind === "policies" ? "propostas" : "planos";
    try {
      const { data: item } = await request<Policy | Plan>(
        `${kind}/${encodeURIComponent(slug)}/versions/${versionNumber}`,
      );
      const attribution = `Cópia de “${item.version.title}”, por @${item.author.username}, versão ${item.version.version_number}. Original: /${path}/${item.slug}?versao=${item.version.version_number}. Revise premissas e fontes antes de publicar.`;
      let body;
      if (kind === "policies") {
        const v = (item as Policy).version;
        body = {
          title: `Cópia — ${v.title}`.slice(0, 200),
          summary: v.summary,
          problem: v.problem,
          proposal: v.proposal,
          category: v.category,
          implementation_start: v.implementation_start,
          implementation_end: v.implementation_end,
          financial_impact_status: v.financial_impact_status,
          impact_justification: v.impact_justification,
          change_summary: attribution,
          impacts: v.impacts.map((r) => ({
            year: r.year,
            impact_type: r.impact_type,
            amount: r.amount,
            description: r.description,
            ...fiscalMetadataBody(r),
          })),
          fundings: v.fundings.map((r) => ({
            funding_type: r.funding_type,
            amount: r.amount,
            year: r.year,
            description: r.description,
          })),
          sources: v.sources.map((r) => ({
            source_id: r.source.id,
            usage_description: r.usage_description,
          })),
        };
      } else {
        const v = (item as Plan).version;
        body = {
          title: `Cópia — ${v.title}`.slice(0, 200),
          summary: v.summary,
          vision: v.vision,
          start_year: v.start_year,
          end_year: v.end_year,
          fiscal_scenario: fiscalScenarioBody(v.fiscal_scenario),
          change_summary: attribution,
          policies: v.policies.map((r) => ({
            policy_version_id: r.policy_version_id,
            is_enabled: r.is_enabled,
          })),
        };
      }
      const result = await request<Policy | Plan>(kind, {
        method: "POST",
        body: JSON.stringify(body),
      });
      router.push(`/painel/${path}/${result.data.id}`);
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "Não deu para copiar. Tente de novo.",
      );
      setBusy(false);
    }
  }
  return (
    <>
      {!user && !loading ? (
        <Link
          className="copy-button"
          href="/entrar"
          title="Entre na sua conta para criar uma cópia privada"
        >
          <Icon name="copy" /> Entrar para duplicar
        </Link>
      ) : (
        <button
          className="copy-button"
          disabled={loading || busy}
          onClick={duplicate}
        >
          <Icon name="copy" />
          {busy ? "Criando cópia…" : "Duplicar"}
        </button>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </>
  );
}
export function CardActions({
  kind,
  slug,
  versionNumber,
}: {
  kind: "policies" | "plans";
  slug: string;
  versionNumber: number;
}) {
  const [shared, setShared] = useState("");
  return (
    <div className="card-actions">
      <button disabled title="Apoios ainda não estão disponíveis">
        <Icon name="heart" />
        Apoiar
      </button>
      <button disabled title="Comentários ainda não estão disponíveis">
        <Icon name="comment" />
        Comentar
      </button>
      <DuplicateButton kind={kind} slug={slug} versionNumber={versionNumber} />
      <button
        onClick={async () => {
          const url = `${window.location.origin}/${kind === "policies" ? "propostas" : "planos"}/${slug}?versao=${versionNumber}`;
          try {
            if (navigator.share) await navigator.share({ url });
            else {
              await navigator.clipboard.writeText(url);
              setShared("Link copiado.");
            }
          } catch {
            setShared(
              "Não deu para compartilhar. Abra a publicação e copie o endereço.",
            );
          }
        }}
      >
        Compartilhar ↗
      </button>
      {shared && <p role="status">{shared}</p>}
      <p className="action-note muted">
        Apoios e comentários em breve. Duplicar cria um rascunho privado.
      </p>
    </div>
  );
}
