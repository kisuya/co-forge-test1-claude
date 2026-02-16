import { describe, it, expect } from "vitest";

describe("AlertBadge component", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/components/AlertBadge");
    expect(mod.default).toBeDefined();
  });
});

describe("ReportView component", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/components/ReportView");
    expect(mod.default).toBeDefined();
  });
});

describe("Reports list page", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/app/reports/page");
    expect(mod.default).toBeDefined();
  });
});

describe("Report detail page", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/app/reports/[id]/page");
    expect(mod.default).toBeDefined();
  });
});

describe("Reports by stock page", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/app/reports/stock/[stockId]/page");
    expect(mod.default).toBeDefined();
  });
});
