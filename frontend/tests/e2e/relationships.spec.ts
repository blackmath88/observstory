import { expect, test } from "@playwright/test";
import fixture from "../../fixtures/relationships/knowledge.json" with { type: "json" };

test("relationship evidence qualifies unresolved, missing and malformed links with keyboard navigation", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/workspace/data/knowledge.json", (route) => route.fulfill({ json: fixture }));
  await page.goto("/workspace/#/?view=board&focus=research&group=lifecycle&range=fit&item=research");
  let panel = page.getByRole("region", { name: /Published relationships/ });
  await expect(panel).toContainText("Knowledge is partial");
  await expect(panel).toContainText("2 published link(s) have no available endpoint");
  await expect(panel).toContainText("Exporter endpoint check: unresolved");
  await expect(panel).toContainText("Some published relationship fields are unreadable");
  const first = panel.locator("article").first();
  await first.getByText("Inspect link evidence", { exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(first.getByRole("blockquote")).toHaveText("Source claim, not an accepted decision.");
  await expect(first).toContainText("Producer did not find this quote at export.");
  await expect(first.getByRole("link", { name: /Inspect manifest/ })).toHaveAttribute(
    "href",
    /blob\/1111111111111111111111111111111111111111\/\.observstory\/knowledge.json$/,
  );
  await panel.locator("article").nth(1).getByText("Inspect link evidence", { exact: true }).click();
  await expect(panel).toContainText("Quote match was not checked.");
  await expect(panel.locator('a[href^="javascript:"]')).toHaveCount(0);
  await panel.getByRole("button", { name: "Open related record: Proposed concept" }).focus();
  await page.keyboard.press("Enter");
  panel = page.getByRole("region", { name: /Published relationships/ });
  await expect(page.getByRole("dialog").getByRole("heading", { name: "Proposed concept", exact: true })).toBeVisible();
  await expect(panel).toContainText("missing-record · unavailable here");
  await expect(panel).toContainText("Exporter endpoint check: both present");
  await expect(panel.getByRole("button", { name: /missing-record/ })).toHaveCount(0);
  await expect(page).toHaveURL(/focus=research/);
  await expect(page).toHaveURL(/group=lifecycle/);
  await page.reload();
  await expect(panel).toBeVisible();
  await page.getByRole("button", { name: "Back to workspace" }).click();
  await expect(page.locator(".board-card")).toHaveCount(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});

test("real published research links retain quoted provenance and navigate the shared drawer", async ({ page }, testInfo) => {
  test.skip(!process.env.OBSERVSTORY_LIVE_DATA, "Requires captured Open Presence data");
  await page.goto("/live/#/?view=board&focus=research&item=research-pdf-history-claims");
  let panel = page.getByRole("region", { name: /Published relationships/ });
  await expect(panel).toContainText("Project knowledge · source declared");
  await expect(panel.locator(".relationship-verb")).toHaveText("qualifies →");
  await panel.getByText("Inspect link evidence", { exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(panel.getByRole("blockquote")).toHaveText("The imported report is research input, not a verified source ledger.");
  await expect(panel).toContainText("Producer found this quote at export.");
  await expect(panel.getByRole("link").first()).toHaveAttribute("href", /blob\/b1af0128bfd48e5d6e8b8579f790858636b7d087\/.*CLAIMS.md#L5$/);
  await panel.locator(".relationship-quote").scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath("open-presence-relationship-quote.png") });
  await panel.getByRole("button", { name: /Open related record:/ }).focus();
  await page.keyboard.press("Enter");
  panel = page.getByRole("region", { name: /Published relationships/ });
  await expect(panel.locator("article")).toHaveCount(2);
  await expect(panel.locator(".relationship-verb")).toHaveText(["qualifies →", "informs →"]);
  await panel.getByRole("button", { name: /Open related record: PDF history/ }).click();
  await expect(panel.locator("article")).toHaveCount(1);
  await expect(panel.locator(".relationship-current")).toContainText("PDF history");
  await page.getByRole("button", { name: /Reveal in Overview/ }).click();
  await expect(page.locator(".reveal-notice")).toContainText(/outside/i);
  await expect(page).toHaveURL(/focus=research/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("real manifest links stay distinct from quotes and membership", async ({ page }, testInfo) => {
  test.skip(!process.env.OBSERVSTORY_LIVE_DATA, "Requires captured Open Presence data");
  await page.goto("/live/#/?item=concept-human-signal");
  const panel = page.getByRole("region", { name: /Published relationships/ });
  await expect(panel.locator("article")).toHaveCount(4);
  const manifest = panel.locator("article").filter({ hasText: "manifest declared" }).first();
  await manifest.getByText("Inspect link evidence", { exact: true }).click();
  await expect(manifest).toContainText("No quoted passage supplied for this manifest link.");
  await expect(manifest.getByRole("link", { name: /Inspect manifest/ })).toHaveAttribute(
    "href",
    /blob\/b1af0128bfd48e5d6e8b8579f790858636b7d087\/\.observstory\/knowledge.json$/,
  );
  await expect(page.getByRole("navigation", { name: "Workspace locations" })).toBeVisible();
  await manifest.getByRole("link", { name: /Inspect manifest/ }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath("open-presence-manifest-relationship.png") });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
