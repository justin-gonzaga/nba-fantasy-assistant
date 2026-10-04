export const FX_BUDGET_GZIP: number
export function evaluate(
  files: { name: string; text: string }[],
  fxGzip: number,
  budget?: number,
): { ok: boolean; message: string }
