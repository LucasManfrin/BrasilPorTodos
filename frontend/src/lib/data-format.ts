import type { Indicator } from "./indicator-types";
type Decimal = {
    n: bigint;
    scale: number;
};
const ten = (n: number) => BigInt(10) ** BigInt(n);
function decimal(value: string | number): Decimal | null {
    const match = String(value).match(/^([+-]?)(\d+)(?:\.(\d*))?(?:e([+-]?\d+))?$/i);
    if (!match)
        return null;
    const exponent = Number(match[4] ?? 0);
    if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > 40)
        return null;
    const fraction = match[3] ?? "";
    let n = BigInt(match[2] + fraction) * (match[1] === "-" ? BigInt(-1) : BigInt(1));
    const scale = fraction.length - exponent;
    if (scale < 0)
        n *= ten(-scale);
    return { n, scale: Math.max(0, scale) };
}
const abs = (n: bigint) => n < BigInt(0) ? -n : n;
function rounded(n: bigint, denominator: bigint, places: number, fixed = false) {
    const magnitude = (abs(n) * ten(places) + denominator / BigInt(2)) / denominator;
    const digits = magnitude.toString().padStart(places + 1, "0");
    const whole = places ? digits.slice(0, -places) : digits;
    const fraction = places ? digits.slice(-places) : "";
    const tail = fixed ? fraction : fraction.replace(/0+$/, "");
    return (n < BigInt(0) && magnitude ? "−" : "") + whole.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + (tail ? "," + tail : "");
}
const monetary = (unit: string) => /^(R\$|BRL)$/i.test(unit.trim());
export function compactParts(value: string | number, unit = "") {
    const d = decimal(value);
    if (!d)
        return { number: "Sem dado", unit: "", label: "Sem dado" };
    const denominator = ten(d.scale);
    let number: string, suffix = unit;
    if (monetary(unit)) {
        const bands = [[12, "tri", 2], [9, "bi", 1], [6, "mi", 1], [3, "mil", 1]] as const;
        const band = bands.find(([power]) => abs(d.n) >= denominator * ten(power));
        const amount = rounded(abs(d.n), denominator * ten(band?.[0] ?? 0), band?.[2] ?? 2, !band);
        number = (d.n < BigInt(0) ? "−" : "") + "R$ " + amount;
        suffix = band?.[1] ?? "";
    }
    else
        number = rounded(d.n, denominator, 2);
    return { number, unit: suffix, label: number + (suffix ? " " + suffix : "") };
}
/** Decimal strings stay exact; only the displayed result is rounded. */
export function formatCompact(value: string | number, unit = "") {
    return compactParts(value, unit).label;
}
export function formatExact(value: string | number, unit = "") {
    const d = decimal(value);
    if (!d)
        return "Sem dado";
    if (monetary(unit))
        return (d.n < BigInt(0) ? "−" : "") + "R$ " + rounded(abs(d.n), ten(d.scale), 2, true);
    return rounded(d.n, ten(d.scale), Math.min(d.scale, 12)) + (unit ? " " + unit : "");
}
export function referenceLabel(value: string, frequency = "") {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime()))
        return "Referência não informada";
    if (frequency === "DAILY") return dateLabel(value);
    if (frequency === "QUARTERLY")
        return `${Math.floor(parsed.getUTCMonth() / 3) + 1}º tri/${String(parsed.getUTCFullYear()).slice(-2)}`;
    return new Intl.DateTimeFormat("pt-BR", { month: "short", year: "2-digit", timeZone: "UTC" }).format(parsed).replace(".", "").replace(" de ", "/");
}
export function dateLabel(value: string | null | undefined) {
    if (!value || Number.isNaN(new Date(value).getTime()))
        return "Não informada";
    return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "UTC" }).format(new Date(value));
}
export type Trend = {
    direction: "up" | "down" | "flat" | "unknown";
    kind: "points" | "percent" | "absolute" | "unavailable";
    label: string;
    symbol: string;
};
export function getTrend(item: Indicator): Trend {
    const unavailable: Trend = { direction: "unknown", kind: "unavailable", label: "Variação não comparável", symbol: "—" };
    if (!item.latest)
        return unavailable;
    const points = [...(item.series ?? [])].sort((a, b) => a.reference_date.localeCompare(b.reference_date));
    const latestDate = item.latest.reference_date.slice(0, 10);
    const annual = ["desocupacao", "atividade-ibc-br", "renda-trabalho-real", "informalidade", "participacao-forca-trabalho"].includes(item.code);
    const comparisonDate = `${Number(latestDate.slice(0, 4)) - 1}${latestDate.slice(4)}`;
    const before = annual ? points.find(p => p.reference_date.slice(0, 10) === comparisonDate) : points.filter(p => p.reference_date.slice(0, 10) < latestDate).at(-1);
    if (!before)
        return unavailable;
    const current = decimal(item.latest.value), previous = decimal(before.value);
    if (!current || !previous)
        return unavailable;
    const scale = Math.max(current.scale, previous.scale);
    const a = current.n * ten(scale - current.scale), b = previous.n * ten(scale - previous.scale), delta = a - b;
    const direction = delta > BigInt(0) ? "up" : delta < BigInt(0) ? "down" : "flat";
    const verb = direction === "up" ? "Subiu" : direction === "down" ? "Caiu" : "Sem mudança";
    const symbol = direction === "up" ? "↗" : direction === "down" ? "↘" : "→";
    const context = `vs. ${referenceLabel(before.reference_date, item.frequency)}`;
    const tinyDifference = delta !== BigInt(0) && abs(delta) * BigInt(100) < ten(scale);
    if (item.unit.trim().startsWith("%"))
        return { direction, symbol, kind: "points", label: `${verb} ${tinyDifference ? "menos de 0,01" : rounded(abs(delta), ten(scale), 2)} p.p. ${context}` };
    // Avoid unstable relative percentages around zero, deficits and sign changes.
    const threshold = monetary(item.unit) ? ten(scale) : ten(scale) / BigInt(100);
    if (a > BigInt(0) && b > BigInt(0) && a >= threshold && b >= threshold)
        return { direction, symbol, kind: "percent", label: `${verb} ${delta !== BigInt(0) && abs(delta) * BigInt(10000) < b ? "menos de 0,01" : rounded(abs(delta) * BigInt(100), b, 2)}% ${context}` };
    const deltaString = `${abs(delta) / ten(scale)}${scale ? "." + (abs(delta) % ten(scale)).toString().padStart(scale, "0") : ""}`;
    return { direction, symbol, kind: "absolute", label: `${verb} ${tinyDifference ? "menos de " + formatCompact("0.01", item.unit) : formatCompact(deltaString, item.unit)} ${context}` };
}
export type DataPoint = {
    reference_date: string;
    value: string;
    revision?: number;
};
export function selectCalendarPeriod<T extends DataPoint>(points: T[], period: "1y" | "5y" | "max"): T[] {
    const unique = new Map<string, T>();
    for (const point of points) {
        const previous = unique.get(point.reference_date);
        if (!previous || (point.revision ?? 0) >= (previous.revision ?? 0))
            unique.set(point.reference_date, point);
    }
    const sorted = [...unique.values()].sort((a, b) => a.reference_date.localeCompare(b.reference_date));
    if (period === "max" || !sorted.length)
        return sorted;
    const last = new Date(sorted.at(-1)!.reference_date);
    const lastMonth = last.getUTCFullYear() * 12 + last.getUTCMonth();
    const firstMonth = lastMonth - (period === "1y" ? 12 : 60) + 1;
    return sorted.filter(point => { const d = new Date(point.reference_date); return d.getUTCFullYear() * 12 + d.getUTCMonth() >= firstMonth; });
}
