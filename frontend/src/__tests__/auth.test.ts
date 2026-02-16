import { describe, it, expect } from "vitest";

describe("Auth Pages", () => {
  it("login page module exists", async () => {
    const mod = await import("@/app/login/page");
    expect(mod.default).toBeDefined();
  });

  it("signup page module exists", async () => {
    const mod = await import("@/app/signup/page");
    expect(mod.default).toBeDefined();
  });
});

describe("Lib modules", () => {
  it("api module exports authApi", async () => {
    const mod = await import("@/lib/api");
    expect(mod.authApi).toBeDefined();
    expect(mod.authApi.signup).toBeDefined();
    expect(mod.authApi.login).toBeDefined();
    expect(mod.authApi.refresh).toBeDefined();
  });

  it("auth module exports helpers", async () => {
    const mod = await import("@/lib/auth");
    expect(mod.getAccessToken).toBeDefined();
    expect(mod.setTokens).toBeDefined();
    expect(mod.clearTokens).toBeDefined();
    expect(mod.isLoggedIn).toBeDefined();
  });
});

describe("Root layout", () => {
  it("layout module exists", async () => {
    const mod = await import("@/app/layout");
    expect(mod.default).toBeDefined();
  });

  it("root page module exists", async () => {
    const mod = await import("@/app/page");
    expect(mod.default).toBeDefined();
  });
});
