import { describe, it, expect } from "vitest";

describe("Dashboard page", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/app/dashboard/page");
    expect(mod.default).toBeDefined();
  });
});

describe("StockCard component", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/components/StockCard");
    expect(mod.default).toBeDefined();
  });
});

describe("StockSearch component", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/components/StockSearch");
    expect(mod.default).toBeDefined();
  });
});

describe("WatchlistManager component", () => {
  it("module exists and exports default", async () => {
    const mod = await import("@/components/WatchlistManager");
    expect(mod.default).toBeDefined();
  });
});

describe("Types", () => {
  it("types module can be imported", async () => {
    const mod = await import("@/types");
    expect(mod).toBeDefined();
  });
});

describe("API queries", () => {
  it("queries module exports stocksApi", async () => {
    const mod = await import("@/lib/queries");
    expect(mod.stocksApi).toBeDefined();
    expect(mod.stocksApi.search).toBeDefined();
  });

  it("queries module exports watchlistApi", async () => {
    const mod = await import("@/lib/queries");
    expect(mod.watchlistApi).toBeDefined();
    expect(mod.watchlistApi.getAll).toBeDefined();
    expect(mod.watchlistApi.add).toBeDefined();
    expect(mod.watchlistApi.remove).toBeDefined();
    expect(mod.watchlistApi.updateThreshold).toBeDefined();
  });

  it("queries module exports reportsApi", async () => {
    const mod = await import("@/lib/queries");
    expect(mod.reportsApi).toBeDefined();
    expect(mod.reportsApi.getAll).toBeDefined();
    expect(mod.reportsApi.getById).toBeDefined();
    expect(mod.reportsApi.getByStock).toBeDefined();
  });
});
