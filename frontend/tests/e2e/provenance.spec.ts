import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import knowledge from "../../fixtures/relationships/knowledge.json" with { type: "json" };

const declaration = JSON.parse(readFileSync(new URL("../../fixtures/workspace/data/workspace.json", import.meta.url), "utf8"));

test("drawer provenance qualifies partial, mismatched and unavailable captures", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/workspace/data/knowledge.json", (route) => route.fulfill({ json: knowledge }));
  await page.route("**/workspace/data/workspace.json", (route) =>
    route.fulfill({ json: { ...declaration, source_commit: "2".repeat(40) } }),
  );
  await page.route("**/workspace/data/scene.json", (route) => route.fulfill({ status: 404, body: "missing" }));
  await page.goto("/workspace/#/?view=board&focus=research&item=research");
  const panel = page.getByRole("region", { name: "Sources and provenance" });
  await expect(panel).toContainText("No source material linked.");
  await expect(panel).toContainText("Captured input revisions differ.");
  await expect(panel).toContainText("Knowledge export is partial");
  await expect(panel).toContainText("Scene: missing. Its evidence is unavailable.");
  await panel.getByText("Captured input revisions", { exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(panel.locator("code")).toContainText(["1".repeat(40), "2".repeat(40)]);
  const scene = panel.locator(".source-capture-row").filter({ hasText: "Scene" });
  await expect(scene).toContainText("Immutable revision unavailable");
  await expect(scene).toContainText("Generation time unavailable");
  await expect(scene.locator("code")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator(".board-card")).toHaveCount(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});

test("real drawer provenance preserves sources and exact captured revisions", async ({ page }, testInfo) => {
  test.skip(!process.env.OBSERVSTORY_LIVE_DATA, "Requires captured public Open Presence inputs");
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/live/#/?view=board&focus=research&item=research-pdf-history-claims");
  const panel = page.getByRole("region", { name: "Sources and provenance" });
  await expect(panel.getByRole("link")).toHaveAttribute(
    "href",
    /blob\/b1af0128bfd48e5d6e8b8579f790858636b7d087\/modules\/pdf-history\/research\/CLAIMS.md$/,
  );
  await expect(panel.locator(".source-caution")).toHaveCount(0);
  await panel.getByText("Captured input revisions", { exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(panel.locator("code")).toHaveText(Array(3).fill("b1af0128bfd48e5d6e8b8579f790858636b7d087"));
  await expect(panel).toContainText("Generated 2026-10-31T18:39:07Z");
  await expect(panel.locator(".source-capture-row").filter({ hasText: "Scene" })).toContainText("Immutable revision unavailable");
  await expect(panel.locator(".source-capture-row").filter({ hasText: "Workspace" })).toContainText("Generation time unavailable");
  await panel.locator(".source-capture").scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath("open-presence-provenance.png") });
  await page.reload();
  await expect(panel).toBeVisible();
  await expect(page).toHaveURL(/focus=research/);
  await page.getByRole("button", { name: "Back to workspace" }).click();
  await expect(page.locator(".board-card")).toHaveCount(7);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});
