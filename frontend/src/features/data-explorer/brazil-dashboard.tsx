"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { Indicator } from "@/lib/indicator-types";
import type { FiscalBaseline, FiscalComposition, FiscalInterest, FunctionalSpending, GeneralGovernment } from "@/lib/types";
import type { CSSProperties } from "react";
import { formatCompact, formatExact, dateLabel } from "@/lib/data-format";
import { CollectionStatusBar, type CollectionStatus } from "@/components/collection-status";
import { EmptyState } from "@/components/page-kit";
import { IndicatorTile } from "./indicator-tile";
import { IndicatorDrawer } from "./indicator-drawer";
import { responsiveCardSpans } from "./balanced-grid";
import { groupSources } from "./source-helpers";
import styles from "./dashboard.module.css";
import { FiscalCompositionPanel } from "./fiscal-composition-panel";
import { FiscalInterestPanel } from "./fiscal-interest-panel";
import { FunctionalSpendingPanel } from "./functional-spending-panel";
import { GeneralGovernmentPanel } from "./general-government-panel";
const themes = [
    { id: "employment", name: "Emprego e renda", text: "Desemprego, renda, informalidade e participação: leia esses recortes juntos.", codes: ["desocupacao", "renda-trabalho-real", "informalidade", "participacao-forca-trabalho"], missing: [] },
    { id: "prices", name: "Preços e juros", text: "O mês, os últimos 12 meses e a taxa de juros mostram recortes diferentes.", codes: ["ipca-mensal", "ipca-12-meses", "selic-meta"], missing: [] },
    { id: "activity", name: "Atividade econômica", text: "Produção e tamanho da economia. Valores nominais não medem crescimento real.", codes: ["atividade-ibc-br", "pib-nominal-trimestral"], missing: ["PIB em volume: crescimento real ainda em preparação."] },
    { id: "accounts", name: "Contas do governo", text: "Receita, despesa e saldo primário do Governo Central. Sem juros, estados ou municípios.", codes: ["rtn-receita-liquida", "rtn-despesa-primaria", "rtn-resultado-primario"], missing: [] },
    { id: "debt", name: "Dívida", text: "Bruta e líquida têm definições diferentes. Ambas usam o PIB como referência.", codes: ["divida-bruta-pib", "divida-liquida-pib"], missing: [] }
];
// Fixed roles, never ranked by an improvement or a political interpretation.
const highlights = [
    { code: "desocupacao", variant: "blue" as const },
    { code: "ipca-mensal", variant: "yellow" as const },
    { code: "divida-bruta-pib", variant: "green" as const },
    { code: "rtn-resultado-primario", variant: "night" as const }
];
function highlightContext(item: Indicator, items: Indicator[]) {
    const value = (code: string, samePeriod = false) => {
        const related = items.find(candidate => candidate.code === code);
        return related?.latest && (!samePeriod || related.latest.reference_date === item.latest?.reference_date)
            ? `${formatCompact(related.latest.value, related.unit)}` : "ainda indisponível neste recorte";
    };
    if (item.code === "desocupacao") return "Leia com renda, informalidade e participação no trabalho. Confira esses recortes na seção Emprego e renda.";
    if (item.code === "ipca-mensal") return `Outros recortes: inflação em 12 meses ${value("ipca-12-meses")}; Selic ${value("selic-meta")}. Cada série tem sua própria referência.`;
    if (item.code === "divida-bruta-pib") return `Compare com a dívida líquida: ${value("divida-liquida-pib", true)}. As definições de dívida são diferentes.`;
    return `No mesmo mês: receita ${value("rtn-receita-liquida", true)}; despesa ${value("rtn-despesa-primaria", true)}. Este saldo não inclui juros.`;
}
export function BrazilDashboard({ items, status, fiscal, composition, interest, spending, government }: {
    items: Indicator[] | null;
    status: CollectionStatus | null;
    fiscal?: FiscalBaseline | null;
    composition?: FiscalComposition | null;
    interest?: FiscalInterest | null;
    spending?: FunctionalSpending | null;
    government?: GeneralGovernment | null;
}) {
    const rootRef = useRef<HTMLDivElement>(null);
    const filtersRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        const root = rootRef.current, filters = filtersRef.current;
        if (!root || !filters) return;
        const html = document.documentElement;
        const previousPadding = html.style.scrollPaddingTop;
        const header = document.querySelector(".site-header");
        const measure = () => {
            const headerHeight = header?.getBoundingClientRect().height ?? 80;
            const filterHeight = filters.getBoundingClientRect().height;
            root.style.setProperty("--filter-height", String(filterHeight) + "px");
            html.style.scrollPaddingTop = String(headerHeight) + "px";
        };
        measure();
        const observer = new ResizeObserver(measure);
        observer.observe(filters);
        if (header) observer.observe(header);
        return () => { observer.disconnect(); html.style.scrollPaddingTop = previousPadding; };
    }, []);
    const params = useSearchParams();
    const [search, setSearch] = useState(params.get("q") ?? "");
    const [query, setQuery] = useState(search);
    const [theme, setTheme] = useState(params.get("theme") ?? "");
    const [category, setCategory] = useState(params.get("category") ?? "");
    const [selected, setSelected] = useState<Indicator | null>(null);
    useEffect(() => { const timer = setTimeout(() => setQuery(search), 300); return () => clearTimeout(timer); }, [search]);
    useEffect(() => { const next = new URLSearchParams(); if (query)
        next.set("q", query); if (theme)
        next.set("theme", theme); if (category)
        next.set("category", category); window.history.replaceState(null, "", `/brasil${next.size ? "?" + next : ""}`); }, [query, theme, category]);
    const filtered = useMemo(() => (items ?? []).filter(item => {
        const topic = themes.find(group => group.codes.includes(item.code));
        return (!theme || topic?.id === theme) && (!category || item.category === category) && (!query || `${item.name} ${item.description} ${item.latest?.source.institution ?? ""}`.toLocaleLowerCase("pt-BR").includes(query.toLocaleLowerCase("pt-BR")));
    }), [items, query, theme, category]);
    const active = Boolean(query || theme || category);
    const featured = active ? [] : highlights.flatMap(config => { const item = filtered.find(item => item.code === config.code); return item ? [{ item, ...config }] : []; });
    function clear() { setSearch(""); setQuery(""); setTheme(""); setCategory(""); }
    return <div ref={rootRef} className={styles.dashboard}>
    {featured.length > 0 && <section aria-labelledby="highlights-title"><div className={styles.sectionHeading}><h2 id="highlights-title">Destaques, com contexto.</h2><p>Emprego, preços, dívida e contas públicas. Sempre os mesmos recortes.</p></div><div className={styles.highlights}>{featured.map(({ item, variant }) => <IndicatorTile key={item.id} item={item} variant={variant} featured context={highlightContext(item, items??[])} onOpen={setSelected}/>)}</div><details className={styles.selectionRule}><summary>Por que estes destaques?</summary><p>A seleção é fixa: desemprego, inflação mensal, dívida bruta/PIB e resultado primário. Ela cobre quatro temas e não muda conforme um número sobe ou cai. Os demais dados e as contrapartidas aparecem por tema abaixo. A seleção não é uma avaliação de governo.</p></details></section>}
    <div className={styles.collection}><CollectionStatusBar key={status?.last_run?.finished_at ?? "initial"} initial={status} compact sourceCount={groupSources(Array.from(new Map((items ?? []).flatMap(item => item.latest ? [[item.latest.source.id, item.latest.source] as const] : [])).values()), items ?? []).length} names={{ ...Object.fromEntries((items ?? []).map(item => [item.code, item.name])), "rtn-composition": "Composição fiscal do Governo Central", "rtn-interest": "Juros e saldo nominal do Governo Central", "federal-spending": "Despesas e transferências federais por função", "general-government": "Estatísticas Fiscais do Governo Geral" }}/></div>
    <div ref={filtersRef} className={styles.filters} role="search" aria-label="Filtrar indicadores">
      <label className={styles.search}><span>Pesquisar indicador</span><input type="search" placeholder="Nome, assunto ou instituição" value={search} onChange={event => setSearch(event.target.value)}/></label>
      <div className={styles.chips} aria-label="Temas"><button className={`button ${!theme && !category ? styles.active : ""}`} aria-pressed={!theme && !category} onClick={() => { setTheme(""); setCategory(""); }}>Todos</button>{themes.map(group => <button key={group.id} className={`button ${theme === group.id ? styles.active : ""}`} aria-pressed={theme === group.id} onClick={() => { setTheme(group.id); setCategory(""); }}>{group.name}</button>)}</div>
      <div className={styles.filterCount} role="status">{filtered.length} {filtered.length === 1 ? "indicador" : "indicadores"}{active && <button className="button secondary" onClick={clear}>Limpar</button>}</div>
    </div>
    {!items ? <EmptyState error title="Os dados deram uma pausa." description="Não conseguimos acessar o catálogo completo. Tente novamente." href="/brasil" action="Tentar de novo"/> : !filtered.length ? <EmptyState title="Nenhum indicador encontrado" description="Tente outro nome ou limpe os filtros. Um dado ausente nunca vira zero." href="/brasil" action="Limpar filtros"/> : query.trim() ? <section className={styles.topic} aria-labelledby="search-results-title"><div className={styles.sectionHeading}><h2 id="search-results-title">Resultados da busca</h2><p>Os indicadores encontrados, juntos na mesma grade.</p></div><ThemeGrid members={filtered} onOpen={setSelected}/></section> : themes.map(group => {
            const members = filtered.filter(item => group.codes.includes(item.code));
            if (!members.length) return null;
            return <section key={group.id} className={styles.topic} data-theme={group.id} aria-labelledby={`topic-${group.id}`}><div className={styles.sectionHeading}><h2 id={`topic-${group.id}`}>{group.name}</h2><p>{group.text}</p></div><ThemeGrid members={members} onOpen={setSelected}/>{!active && group.missing.map(text => <p className={styles.preparationNote} key={text}>{text}</p>)}</section>;
        })}
    {!query.trim() && filtered.some(item => !themes.some(group => group.codes.includes(item.code))) && <section className={styles.topic}><div className={styles.sectionHeading}><h2>Outros indicadores</h2></div><ThemeGrid members={filtered.filter(item => !themes.some(group => group.codes.includes(item.code)))} onOpen={setSelected}/></section>}
    <FiscalOverview fiscal={fiscal} composition={composition} interest={interest} spending={spending} government={government}/>
    <aside className={styles.context}><h2>Um número não conta a história toda.</h2><p>As setas mostram direção, não se algo é bom ou ruim. Para discutir causas, compare outros indicadores e confira a análise usada.</p><Link href="/metodologia">Como tratamos dados e hipóteses →</Link></aside>
    <IndicatorDrawer item={selected} onClose={() => setSelected(null)}/>
  </div>;
}
function ThemeGrid({ members, onOpen }: { members: Indicator[]; onOpen: (item: Indicator) => void }) {
    return <div className={styles.bento} data-card-count={members.length}>{members.map((item, index) => {
        const spans = responsiveCardSpans(members.length, index);
        const style = { "--card-span-mobile": spans.mobile, "--card-span-tablet": spans.tablet, "--card-span-desktop": spans.desktop, "--card-span-wide": spans.wide } as CSSProperties;
        return <div key={item.id} style={style}><IndicatorTile item={item} highlighted={highlights.some(config => config.code === item.code)} horizontal={spans.tablet === 12 || spans.desktop === 12 || spans.wide === 12} onOpen={onOpen}/></div>;
    })}</div>;
}
function FiscalOverview({ fiscal, composition, interest, spending, government }: {
    fiscal?: FiscalBaseline | null;
    composition?: FiscalComposition | null;
    interest?: FiscalInterest | null;
    spending?: FunctionalSpending | null;
    government?: GeneralGovernment | null;
}) {
    const amounts = fiscal?.status === "AVAILABLE" ? fiscal.amounts : null;
    const max = amounts ? Math.max(Number(amounts.net_revenue), Number(amounts.primary_expenditure)) : 0;
    const ratios = fiscal?.gdp?.status === "AVAILABLE" && fiscal.gdp.year === fiscal.year ? fiscal.ratios : null;
    return <section className={styles.fiscal} aria-labelledby="fiscal-title"><div className={styles.sectionHeading}><h2 id="fiscal-title">A conta antes das propostas.</h2><p>Governo Central · {fiscal?.year ?? "ano ainda não fechado"} · caixa · reais nominais · sem juros</p></div>{amounts ? <><div className={styles.totals}>{[["Receita líquida", amounts.net_revenue, ratios?.net_revenue_pct_gdp], ["Despesa primária", amounts.primary_expenditure, ratios?.primary_expenditure_pct_gdp], ["Resultado primário", amounts.published_primary_balance, ratios?.primary_balance_pct_gdp]].map(([name, value, ratio]) => <div key={name}><h3>{name}</h3><strong title={formatExact(value!, "R$")}>{formatCompact(value!, "R$")}</strong><span>{name === "Resultado primário" ? (!/[1-9]/.test(String(value)) ? "Equilíbrio primário" : String(value).startsWith("-") ? "− Déficit primário" : "Superávit primário") : name === "Receita líquida" ? "Após transferências consideradas na fonte" : "Despesa pelo critério da fonte"}</span>{ratio && <small>{formatCompact(ratio, "% do PIB")}</small>}</div>)}</div><div className={styles.balance} role="img" aria-label={`Comparação de ${fiscal?.year}: receita líquida ${formatCompact(amounts.net_revenue, "R$")} e despesa primária ${formatCompact(amounts.primary_expenditure, "R$")}.`}><div><span>Receita</span><div><i style={{ width: `${max ? Number(amounts.net_revenue) / max * 100 : 0}%` }}/></div></div><div><span>Despesa</span><div><i style={{ width: `${max ? Number(amounts.primary_expenditure) / max * 100 : 0}%` }}/></div></div></div></> : <p>Precisamos de receitas, despesas e resultado compatíveis nos 12 meses de um ano fechado. Dados ausentes não significam zero.</p>}<p>Esta é uma conta observada. O efeito das propostas não é somado automaticamente a ela.</p><details><summary>Confira como a conta foi feita</summary>{amounts && <><p>Receita líquida − despesa primária = {formatExact(amounts.calculated_primary_balance, "R$")}. Publicado: {formatExact(amounts.published_primary_balance, "R$")}. Diferença de reconciliação: {formatExact(amounts.reconciliation_difference, "R$")}.</p><dl>{[["Receita líquida", amounts.net_revenue], ["Despesa primária", amounts.primary_expenditure]].map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{formatExact(value, "R$")}</dd></div>)}</dl></>}{fiscal && <><p>{fiscal.methodology}</p><p>{dateLabel(fiscal.period_start)} a {dateLabel(fiscal.period_end)}. Estados e municípios não estão incluídos. Revisões geram uma nova base e preservam versões publicadas.</p>{fiscal.status === "AVAILABLE" && fiscal.gdp?.status === "AVAILABLE" && fiscal.gdp.year === fiscal.year && fiscal.gdp.nominal_gdp && <p>PIB do mesmo ano: {formatCompact(fiscal.gdp.nominal_gdp, "R$")} ({formatExact(fiscal.gdp.nominal_gdp, "R$")}), soma de quatro trimestres, sujeita a revisão; precisão original de R$ 10 mil. <a href={fiscal.gdp.source.url} target="_blank" rel="noopener noreferrer">Fonte do PIB ↗</a></p>}{fiscal.source && <p><a href={fiscal.source.url} target="_blank" rel="noopener noreferrer">{fiscal.source.title} ↗</a> · {fiscal.source.institution} · <a href={fiscal.source.license_url} target="_blank" rel="noopener noreferrer">{fiscal.source.license}</a></p>}<ul>{Array.from(new Set([...fiscal.limitations, ...(fiscal.gdp?.limitations ?? []), ...fiscal.missing])).map((text, index) => <li key={index}>{text}</li>)}</ul></>}</details><FiscalCompositionPanel fiscal={fiscal} composition={composition}/><FiscalInterestPanel fiscal={fiscal} interest={interest}/><FunctionalSpendingPanel fiscal={fiscal} spending={spending}/><GeneralGovernmentPanel fiscal={fiscal} government={government}/></section>;
}
