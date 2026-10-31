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

test("category and search share URL state across overview, board, drawer and reload", async ({ page }) => {
  await page.goto("/workspace/");
  const researchFocus = page.getByRole("button", { name: /^Research \d/ });
  await researchFocus.focus();
  await page.keyboard.press("Enter");
  const rows = page.locator(".record-button");
  await expect(rows).toHaveCount(2);
  await expect(rows.filter({ hasText: "Undated research" })).toBeVisible();
  await expect(rows.filter({ hasText: "Planned checkpoint" })).toHaveCount(0);
  await page.getByRole("searchbox", { name: "Find records" }).fill("undated");
  await page.getByRole("button", { name: "Board", exact: true }).click();
  await expect(page.locator(".board-card")).toHaveCount(1);
  await page.locator(".board-card").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toContainText("Lifecycle undeclared");
  await page.reload();
  await expect(page.getByRole("searchbox", { name: "Find records" })).toHaveValue("undated");
  await expect(researchFocus).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator(".board-card")).toBeFocused();
  await page.getByRole("searchbox").fill("no-such-source");
  await expect(page.getByRole("heading", { name: "No matching records" })).toBeVisible();
  await expect(page.locator(".board-card")).toHaveCount(0);
  await page.getByRole("button", { name: "Clear filters" }).first().click();
  await expect(page.locator(".board-card")).toHaveCount(5);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("nested membership expands past one level and filters reveal descendants without overwriting preferences", async ({ page }) => {
  await page.route("**/data/workspace.json", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.records.find((r: { id: string }) => r.id === "branch").members = ["deep-research"];
    data.records.push({ id: "deep-research", title: "Nested source experiment", kind: "research" });
    await route.fulfill({ response, json: data });
  });
  await page.goto("/workspace/");
  const parent = page.getByRole("button", { name: "Expand Synthetic · knowledge workspace" });
  await parent.click();
  const branch = page.getByRole("button", { name: "Expand Paused supporting exploration" });
  await branch.click();
  await expect(page.locator(".record-button").filter({ hasText: "Nested source experiment" })).toBeVisible();
  await branch.click();
  await page.getByRole("button", { name: /^Research \d/ }).click();
  await expect(page.locator(".record-button").filter({ hasText: "Nested source experiment" })).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(branch).toHaveAttribute("aria-expanded", "false");
  await expect(parent).toHaveAttribute("aria-expanded", "true");
});

test("real Open Presence sources remain navigable through shared category filters", async ({ page }, testInfo) => {
  test.skip(!process.env.OBSERVSTORY_LIVE_DATA, "Set OBSERVSTORY_LIVE_DATA to captured public consumer inputs");
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/live/");
  await expect(page.getByRole("heading", { name: "Human Signal — discovery and community", exact: true })).toBeVisible();
  await page.getByRole("button", { name: /^Research \d/ }).click();
  await expect(page.locator(".record-button").filter({ hasText: "Claim ledger and verification queue" })).toBeVisible();
  await page.locator(".record-button").filter({ hasText: "Claim ledger and verification queue" }).click();
  const source = page.getByRole("dialog").getByRole("link").first();
  await expect(source).toHaveAttribute("href", /https:\/\/github.com\/blackmath88\/baselhack26-open-presence\/blob\//);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: /^Implementation \d/ }).click();
  await expect(page.locator(".record-button").filter({ hasText: "Repository implementation" })).toBeVisible();
  const trackStarts = await page.locator(".time-track").evaluateAll((tracks) => tracks.map((track) => track.getBoundingClientRect().left));
  expect(Math.max(...trackStarts) - Math.min(...trackStarts)).toBeLessThan(1);
  await page.screenshot({ path: testInfo.outputPath("open-presence-implementation.png"), fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});
