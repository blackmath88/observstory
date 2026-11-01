import { expect, test } from "@playwright/test";

test("derived workspace and data-source routes survive reload under a Pages subpath", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/hackathon/");
  await expect(page.locator(".repo-title")).toContainText("northstar/voice-notes");
  await expect(page.getByRole("region", { name: "Workstreams" })).toBeVisible();
  await expect(page.getByText(/Workspace missing/)).toBeVisible();
  await page.getByRole("link", { name: /Data sources/ }).focus();
  await page.keyboard.press("Enter");
  await page.reload();
  await expect(page.getByRole("heading", { name: "Data sources" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("invalid activity remains unavailable", async ({ page }) => {
  await page.goto("/broken/");
  await expect(page.getByText(/Activity is unavailable/)).toBeVisible();
  await expect(page.locator(".counts")).toHaveCount(0);
});

test("synthetic branch keeps origin, resume, selection, focus and expansion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/workspace/");
  const expand = page.getByRole("button", { name: "Expand Synthetic · knowledge workspace" });
  await expand.click();
  const research = page.locator(".record-button").filter({ hasText: "Undated research" });
  await research.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toContainText("No observed event is attached");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(research).toBeFocused();
  await expect(expand).toHaveAttribute("aria-expanded", "true");
  await page.reload();
  await expect(expand).toHaveAttribute("aria-expanded", "true");
  await page.getByRole("button", { name: "Board", exact: true }).click();
  await expect(page.getByRole("heading", { name: /paused/ })).toBeVisible();
  await page.locator(".board-card").filter({ hasText: "Paused supporting exploration" }).click();
  await expect(page.getByRole("dialog")).toContainText("Stopping point");
  await expect(page.getByRole("dialog")).toContainText("Inspect the held-out examples");
  await page.reload();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Back to workspace" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
