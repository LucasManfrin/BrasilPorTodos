/** Collection timestamps are instants; indicator reference dates remain calendar dates. */
export function collectionTimestamp(value: string, timeZone = "America/Sao_Paulo"): string {
  const instant = new Date(value);
  if (!Number.isFinite(instant.getTime())) return "horário indisponível";
  try {
    const parts = new Intl.DateTimeFormat("pt-BR", {
      timeZone, day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    }).formatToParts(instant);
    const read = (type: Intl.DateTimeFormatPartTypes) => parts.find(part => part.type === type)?.value ?? "";
    const zone = timeZone === "America/Sao_Paulo" ? "São Paulo" : timeZone;
    return `${read("day")}/${read("month")}/${read("year")} às ${read("hour")}:${read("minute")} (${zone})`;
  } catch {
    return "horário indisponível";
  }
}
