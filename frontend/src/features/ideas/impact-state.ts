export type SensitivityPercentages = { cost_low: string; cost_high: string; gain_low: string; gain_high: string };
export const defaultPercentages: SensitivityPercentages = { cost_low: "100", cost_high: "100", gain_low: "100", gain_high: "100" };

/** Percentages are decimal strings; no money or multiplier crosses binary floating point. */
export function percentageMultiplier(value: string): string {
  const match = value.trim().match(/^(\d{1,3})(?:[.,](\d{1,2}))?$/);
  if (!match) throw new Error("Use um percentual entre 0 e 200, com até duas casas decimais.");
  const hundredths = BigInt(match[1]) * BigInt(100) + BigInt((match[2] ?? "").padEnd(2, "0"));
  if (hundredths > BigInt(20000)) throw new Error("O percentual precisa ficar entre 0 e 200.");
  return `${hundredths / BigInt(10000)}.${String(hundredths % BigInt(10000)).padStart(4, "0")}`;
}
export function sensitivityAssumptions(input: SensitivityPercentages): SensitivityPercentages {
  const result = Object.fromEntries(Object.entries(input).map(([key, value]) => [key, percentageMultiplier(value)])) as SensitivityPercentages;
  for (const key of ["cost_low", "gain_low"] as const) {
    if (BigInt(result[key].replace(".", "")) > BigInt(10000)) throw new Error("Os limites mínimos devem ser menores ou iguais a 100%.");
  }
  for (const key of ["cost_high", "gain_high"] as const) {
    if (BigInt(result[key].replace(".", "")) < BigInt(10000)) throw new Error("Os limites máximos devem ser maiores ou iguais a 100%.");
  }
  return result;
}
