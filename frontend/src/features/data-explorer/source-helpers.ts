import type { Source } from "@/lib/types";
import type { CollectionStatus } from "@/components/collection-status";

export type DirectoryIndicator = {
  code: string;
  name: string;
  frequency: string;
  latest: {
    reference_date: string;
    source: Source;
    provenance?: { dataset_url?: string };
  } | null;
};
export type SourceMetric = {
  code: string;
  name: string;
  frequency: string;
  referenceDate: string | null;
};
export type DirectorySource = {
  identity: string;
  institution: string;
  officialSite: string | null;
  source: Source;
  records: Source[];
  metrics: SourceMetric[];
  hasUsage: boolean;
  usageCount: number | null;
};
export type SourceFilters = { q?: string; institution?: string; source_type?: string };
export const sourceKinds: Record<string, string> = {
  OFFICIAL: "Dados oficiais",
  LEGISLATION: "Legislação",
  SCIENTIFIC_STUDY: "Estudos científicos",
  TECHNICAL_REPORT: "Relatórios técnicos",
  INSTITUTIONAL_REPORT: "Relatórios institucionais",
  JOURNALISM: "Jornalismo",
  OTHER: "Outras referências",
};
export const normalizeSourceText = (value: string) =>
  value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();

const reviewed = [
  { institution: "Secretaria do Tesouro Nacional", site: "https://www.tesourotransparente.gov.br/", host: "www.tesourotransparente.gov.br", path: "/publicacoes/estatisticas-fiscais-do-governo-geral", id: "tesouro:general-government", codes: [] },
  { institution: "Secretaria do Tesouro Nacional", site: "https://www.tesourotransparente.gov.br/", host: "www.tesourotransparente.gov.br", path: "/ckan/dataset/despesas-e-transferencias-totais", id: "tesouro:federal-spending", codes: [] },
  { institution: "IBGE", site: "https://www.ibge.gov.br/", host: "sidra.ibge.gov.br", path: "/tabela/6390", id: "ibge:6390:5933", codes: ["renda-trabalho-real"] },
  { institution: "IBGE", site: "https://www.ibge.gov.br/", host: "sidra.ibge.gov.br", path: "/tabela/8513", id: "ibge:8513:12466", codes: ["informalidade"] },
  { institution: "IBGE", site: "https://www.ibge.gov.br/", host: "sidra.ibge.gov.br", path: "/tabela/5944", id: "ibge:5944:4096", codes: ["participacao-forca-trabalho"] },
  { institution: "Banco Central do Brasil", site: "https://www.bcb.gov.br/", host: "dadosabertos.bcb.gov.br", path: "/dataset/432-", id: "bcb:432", codes: ["selic-meta"] },
  { institution: "Banco Central do Brasil", site: "https://www.bcb.gov.br/", host: "dadosabertos.bcb.gov.br", path: "/dataset/13762-", id: "bcb:13762", codes: ["divida-bruta-pib"] },
  { institution: "Banco Central do Brasil", site: "https://www.bcb.gov.br/", host: "dadosabertos.bcb.gov.br", path: "/dataset/4513-", id: "bcb:4513", codes: ["divida-liquida-pib"] },
  { institution: "Banco Central do Brasil", site: "https://www.bcb.gov.br/", host: "dadosabertos.bcb.gov.br", path: "/dataset/24363-", id: "bcb:24363", codes: ["atividade-ibc-br"] },
  { institution: "IBGE", site: "https://www.ibge.gov.br/", host: "sidra.ibge.gov.br", path: "/tabela/6381", id: "ibge:6381:4099", codes: ["desocupacao"] },
  { institution: "IBGE", site: "https://www.ibge.gov.br/", host: "sidra.ibge.gov.br", path: "/tabela/1846", id: "ibge:1846:585:90707", codes: ["pib-nominal-trimestral"] },
  { institution: "Secretaria do Tesouro Nacional", site: "https://www.tesourotransparente.gov.br/", host: "www.tesourotransparente.gov.br", path: "/ckan/dataset/resultado-do-tesouro-nacional", id: "tesouro:rtn", codes: ["rtn-receita-liquida", "rtn-despesa-primaria", "rtn-resultado-primario"] },
];

const cohortCollections: Record<string, string> = { "tesouro:federal-spending": "federal-spending", "tesouro:general-government": "general-government" };

function reviewedIdentity(source: Source, indicators: DirectoryIndicator[]) {
  if (source.is_example || source.source_type !== "OFFICIAL") return null;
  let url: URL;
  try { url = new URL(source.url); } catch { return null; }
  if (url.protocol !== "https:" || url.username || url.password || url.port) return null;
  const institution = normalizeSourceText(source.institution);
  const path = url.pathname.replace(/\/$/, "");
  const entry = reviewed.find(item =>
    normalizeSourceText(item.institution) === institution && url.hostname === item.host &&
    (item.host === "dadosabertos.bcb.gov.br" ? path.startsWith(item.path) : path === item.path),
  );
  if (entry) return entry;
  // The IPCA table has two distinct variables: URL equality alone is insufficient.
  if (institution === "ibge" && url.hostname === "sidra.ibge.gov.br" && path === "/tabela/1737") {
    const direct = indicators.find(item => ["ipca-mensal", "ipca-12-meses"].includes(item.code) && item.latest?.source.id === source.id);
    const title = normalizeSourceText(source.title);
    const code = direct?.code ?? (title === "inflacao no mes" ? "ipca-mensal" : title === "inflacao em 12 meses" ? "ipca-12-meses" : null);
    if (code) return { institution: "IBGE", site: "https://www.ibge.gov.br/", id: `ibge:1737:${code === "ipca-mensal" ? "63" : "2265"}`, codes: [code] };
  }
  return null;
}

/** Deduplicate reviewed presentation identities; never mutate source records or IDs. */
export function groupSources(sources: Source[], indicators: DirectoryIndicator[], development = false): DirectorySource[] {
  const groups = new Map<string, DirectorySource>();
  for (const source of sources) {
    if (source.is_example && !development) continue;
    const entry = reviewedIdentity(source, indicators);
    const identity = entry?.id ?? `record:${source.id}`;
    let row = groups.get(identity);
    if (!row) {
      row = { identity, institution: entry?.institution ?? source.institution, officialSite: entry?.site ?? null, source, records: [], metrics: [], hasUsage: false, usageCount: null };
      groups.set(identity, row);
    }
    if (!row.records.some(record => record.id === source.id)) row.records.push(source);
    const linked = entry ? indicators.filter(item => entry.codes.includes(item.code)) : indicators.filter(item => item.latest?.source.id === source.id);
    for (const item of linked) {
      if (item.latest?.source.is_example && !development) continue;
      if (!row.metrics.some(metric => metric.code === item.code)) row.metrics.push({ code: item.code, name: item.name, frequency: item.frequency, referenceDate: item.latest?.reference_date ?? null });
    }
  }
  for (const row of groups.values()) {
    row.records.sort((a, b) => b.accessed_at.localeCompare(a.accessed_at) || a.id.localeCompare(b.id));
    row.source = row.records.find(record => cohortCollections[row.identity] && record.collection_code === cohortCollections[row.identity] && reviewedIdentity(record, [])?.id === row.identity) ?? row.records.find(record => indicators.some(item =>
      row.metrics.some(metric => metric.code === item.code) && item.latest?.source.id === record.id,
    )) ?? row.records[0];
    row.hasUsage = row.records.some(source => (source.usage_count ?? 0) > 0);
    // The API has counts, not publication IDs: summing duplicate references could double-count.
    row.usageCount = row.records.length === 1 ? row.source.usage_count ?? 0 : null;
    row.metrics.sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  }
  return [...groups.values()].sort((a, b) => a.institution.localeCompare(b.institution, "pt-BR") || a.source.title.localeCompare(b.source.title, "pt-BR"));
}

export function filterSources(rows: DirectorySource[], filters: SourceFilters) {
  const q = normalizeSourceText(filters.q ?? "");
  return rows.filter(row =>
    (!filters.institution || normalizeSourceText(row.institution) === normalizeSourceText(filters.institution)) &&
    (!filters.source_type || row.source.source_type === filters.source_type) &&
    (!q || normalizeSourceText([row.institution, ...row.records.map(record => `${record.title} ${record.description ?? ""}`), ...row.metrics.map(metric => `${metric.name} ${metric.code}`)].join(" ")).includes(q)),
  );
}

export function sourceFacets(rows: DirectorySource[], filters: SourceFilters) {
  const institutions = new Map<string, number>();
  for (const row of filterSources(rows, { q: filters.q, source_type: filters.source_type })) institutions.set(row.institution, (institutions.get(row.institution) ?? 0) + 1);
  const kinds = new Map<string, number>();
  for (const row of filterSources(rows, { q: filters.q, institution: filters.institution })) kinds.set(row.source.source_type, (kinds.get(row.source.source_type) ?? 0) + 1);
  return { institutions: [...institutions].sort(([a], [b]) => a.localeCompare(b, "pt-BR")), kinds, totalKind: [...kinds.values()].reduce((sum, count) => sum + count, 0) };
}

export function sourceCollectionState(row: DirectorySource, status: CollectionStatus | null, now: number) {
  const base = { timestamp: null as string | null, label: "Sem coleta automática", tone: "neutral" as "neutral" | "success" | "warning" };
  // This output-only marker is proof of a validated stored cohort, not a URL guess.
  const cohortCollection = cohortCollections[row.identity] && row.source.collection_code === cohortCollections[row.identity] && reviewedIdentity(row.source, [])?.id === row.identity;
  const codes = cohortCollection ? [cohortCollections[row.identity]] : row.metrics.map(metric => metric.code);
  if (!codes.length) return base;
  const run = status?.last_run;
  if (!run) return { ...base, label: "Consulta não informada" };
  const states = codes.map(code => run.series[code]?.status);
  if (states.every(state => state === undefined)) return base;
  if (run.status === "RUNNING") return { ...base, label: "Consulta em andamento", tone: "neutral" as const };
  const timestamp = run.finished_at;
  if (!timestamp || !Number.isFinite(Date.parse(timestamp)) || Date.parse(timestamp) > now) return { ...base, label: "Consulta não informada" };
  const age = now - Date.parse(timestamp);
  const failed = states.some(state => state !== "SUCCESS");
  if (failed) return { timestamp, label: "Falhou na última consulta", tone: "warning" as const };
  // The configured interval plus a 24-hour grace period concerns collection,
  // never the publication's reference period or the author's access date.
  const interval = status && Number.isFinite(status.interval_hours) && status.interval_hours > 0 ? status.interval_hours : 24;
  if (age > (interval + 24) * 60 * 60 * 1000) return { timestamp, label: `Desatualizada há ${Math.floor(age / (24 * 60 * 60 * 1000))} dias`, tone: "warning" as const };
  return { timestamp, label: "Consulta atualizada", tone: "success" as const };
}

/** Read every advertised page; a failed/repeated page is an error, not a truncated directory. */
export async function loadDirectoryPages<T extends { id: string }>(path: string, request: (path: string) => Promise<{ data: T[]; pagination?: { page: number; page_size: number; total: number } } | null>): Promise<T[] | null> {
  const items: T[] = [];
  const ids = new Set<string>();
  let page = 1;
  let total: number | null = null;
  do {
    const response = await request(`${path}?page=${page}&page_size=100`);
    if (!response || !Array.isArray(response.data)) return null;
    const pagination = response.pagination;
    if (pagination && (pagination.page !== page || !Number.isSafeInteger(pagination.total) || pagination.total < 0 || !Number.isSafeInteger(pagination.page_size) || pagination.page_size < 1 || response.data.length > pagination.page_size)) return null;
    const advertised = pagination?.total ?? response.data.length;
    if (total !== null && total !== advertised) return null;
    total = advertised;
    if (!response.data.length && items.length < total) return null;
    for (const item of response.data) {
      if (ids.has(item.id)) return null;
      ids.add(item.id);
      items.push(item);
    }
    if (items.length > total) return null;
    page++;
  } while (items.length < total);
  return items;
}
