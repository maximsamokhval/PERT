/**
 * Frontend optimistic PERT calculation utility.
 *
 * NON-AUTHORITATIVE UI PREVIEW ONLY — backend response is the single source of truth.
 * MUST re-sync from backend response on every save (debounce ≤ 2s).
 *
 * Mirrors backend formulas with 3 decimal precision.
 */

/** Round a number to 3 decimal places. */
function round3(value: number): number {
  return Number(value.toFixed(3));
}

export interface PertMetrics {
  t_expected: number;
  spread: number;
  sigma: number;
  variance: number;
  hidden_reserve: number;
  total_effort: number;
  duration_days: number;
}

/**
 * Calculate PERT metrics for a single estimation item.
 *
 * Formulas:
 *   t_expected     = (O + 4*M + P) / 6
 *   spread         = P - O
 *   sigma          = spread / 6
 *   variance       = sigma ** 2
 *   hidden_reserve = spread * k
 *   total_effort   = t_expected + hidden_reserve
 *   duration_days  = total_effort / (FF * hours_per_day)
 *
 * @param optimistic      Optimistic estimate (1-999)
 * @param most_likely     Most likely estimate (1-999)
 * @param pessimistic     Pessimistic estimate (1-999)
 * @param k               Contingency factor (default 0.1)
 * @param focusFactor     Focus factor (0.5-1.0, default 0.8)
 * @param hoursPerDay     Working hours per day (1-12, default 8)
 */
export function calculatePertMetrics(
  optimistic: number,
  most_likely: number,
  pessimistic: number,
  k = 0.1,
  focusFactor = 0.8,
  hoursPerDay = 8,
): PertMetrics {
  if (optimistic < 1 || optimistic > 999) {
    throw new Error(`optimistic must be 1-999, got ${optimistic}`);
  }
  if (most_likely < 1 || most_likely > 999) {
    throw new Error(`most_likely must be 1-999, got ${most_likely}`);
  }
  if (pessimistic < 1 || pessimistic > 999) {
    throw new Error(`pessimistic must be 1-999, got ${pessimistic}`);
  }
  if (!(optimistic <= most_likely && most_likely <= pessimistic)) {
    throw new Error(
      `O <= M <= P violated: ${optimistic}, ${most_likely}, ${pessimistic}`,
    );
  }

  const t_expected = (optimistic + 4 * most_likely + pessimistic) / 6;
  const spread = pessimistic - optimistic;
  const sigma = spread / 6;
  const variance = sigma ** 2;
  const hidden_reserve = spread * k;
  const total_effort = t_expected + hidden_reserve;
  const duration_days = total_effort / (focusFactor * hoursPerDay);

  return {
    t_expected: round3(t_expected),
    spread: round3(spread),
    sigma: round3(sigma),
    variance: round3(variance),
    hidden_reserve: round3(hidden_reserve),
    total_effort: round3(total_effort),
    duration_days: round3(duration_days),
  };
}
