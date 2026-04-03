/**
 * Vitest PERT formula parity test suite.
 *
 * Consumes pert_test_vectors.json (T024b) and verifies that
 * frontend/src/features/items/utils/pert-calc.ts produces identical
 * results for all 1000 test vectors.
 *
 * This ensures frontend/JS parity with backend/Python calculations.
 */

import { describe, it, expect } from "vitest";
import { calculatePertMetrics } from "@/features/items/utils/pert-calc";

// Load shared test vectors (T024b) — copied from backend/tests/fixtures
// eslint-disable-next-line @typescript-eslint/no-require-imports
import testVectorsJson from "../fixtures/pert_test_vectors.json";

interface TestVector {
  o: number;
  m: number;
  p: number;
  k: number;
  ff: number;
  h: number;
  t_expected: number;
  spread: number;
  sigma: number;
  variance: number;
  hidden_reserve: number;
  total_effort: number;
  duration_days: number;
}

const testVectors: TestVector[] = (
  testVectorsJson as { vectors: TestVector[] }
).vectors;

describe("PERT formula parity (backend ↔ frontend)", () => {
  it("matches all 1000 shared test vectors", () => {
    expect(testVectors.length).toBeGreaterThanOrEqual(1000);

    for (const v of testVectors) {
      const result = calculatePertMetrics(v.o, v.m, v.p, v.k, v.ff, v.h);

      expect(result.t_expected).toBeCloseTo(v.t_expected, 2);
      expect(result.spread).toBeCloseTo(v.spread, 2);
      expect(result.sigma).toBeCloseTo(v.sigma, 2);
      expect(result.variance).toBeCloseTo(v.variance, 2);
      expect(result.hidden_reserve).toBeCloseTo(v.hidden_reserve, 2);
      expect(result.total_effort).toBeCloseTo(v.total_effort, 2);
      expect(result.duration_days).toBeCloseTo(v.duration_days, 2);
    }
  });

  it("handles spec verification example: O=2, M=4, P=8", () => {
    const result = calculatePertMetrics(2, 4, 8, 0.1, 0.8, 8);

    expect(result.t_expected).toBe(4.333);
    expect(result.spread).toBe(6);
    expect(result.sigma).toBe(1);
    expect(result.variance).toBe(1);
    expect(result.hidden_reserve).toBe(0.6);
    expect(result.total_effort).toBe(4.933);
    expect(result.duration_days).toBeCloseTo(0.771, 2);
  });

  it("rejects O > M with error", () => {
    expect(() => calculatePertMetrics(10, 5, 15)).toThrow(
      "O <= M <= P violated",
    );
  });

  it("rejects M > P with error", () => {
    expect(() => calculatePertMetrics(5, 10, 8)).toThrow(
      "O <= M <= P violated",
    );
  });

  it("rejects values below minimum", () => {
    expect(() => calculatePertMetrics(0, 5, 10)).toThrow(
      "optimistic must be 1-999",
    );
  });

  it("rejects values above maximum", () => {
    expect(() => calculatePertMetrics(1000, 1000, 1000)).toThrow(
      "optimistic must be 1-999",
    );
  });
});
