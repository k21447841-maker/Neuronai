import { test, expect } from "@playwright/test";

test.describe("NEUROFLOW AI E2E Smoke", () => {
  test("unauthenticated visitor is redirected to /auth", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/auth/);
    await expect(page.getByText("NEUROFLOW AI")).toBeVisible();
  });

  test("auth screen switches between login, register, and reset", async ({ page }) => {
    await page.goto("/auth");
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(page.getByRole("button", { name: "Create Account" })).toBeVisible();
    await page.getByRole("button", { name: "Forgot password?" }).click();
    await expect(page.getByRole("button", { name: "Send Reset Link" })).toBeVisible();
  });
});
