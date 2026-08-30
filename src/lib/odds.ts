/**
 * All odds are stored and combined as decimal (European) odds. A coupon's
 * total_odds is the product of its legs. Units, never pounds:
 * a stake of 1 unit returns total_odds units, i.e. profit of (total_odds - 1).
 */

export function combineOdds(legOdds: number[]): number {
  return legOdds.reduce((acc, o) => acc * o, 1);
}

export function unitsReturn(totalOdds: number): number {
  return totalOdds - 1;
}

export function formatUnits(units: number): string {
  const sign = units > 0 ? "+" : units < 0 ? "" : "";
  return `${sign}${units.toFixed(1)}u`;
}

export function formatOdds(decimal: number): string {
  return decimal.toFixed(2);
}

/** Actual units a settled coupon returned; 0 if still open/locked. */
export function couponUnits(coupon: { status: string; total_odds: number }): number {
  if (coupon.status === "won") return unitsReturn(coupon.total_odds);
  if (coupon.status === "lost" || coupon.status === "mixed") return -1;
  return 0;
}

/** Rough decimal -> fractional string for players used to bet365-style odds. */
export function formatFractional(decimal: number): string {
  const frac = decimal - 1;
  if (frac <= 0) return "0/1";
  const denominator = 100;
  let numerator = Math.round(frac * denominator);
  let d = denominator;
  const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
  const g = gcd(numerator, d) || 1;
  numerator /= g;
  d /= g;
  return `${numerator}/${d}`;
}
