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

test("drawer locations preserve multiple membership routes and reveal without changing expansion", async ({ page }) => {
  await page.route("**/data/workspace.json", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.records.find((r: { id: string }) => r.id === "branch").members = ["deep-research"];
    data.records.push({ id: "deep-research", title: "Nested source experiment", kind: "research" });
    data.records.push({ id: "other", title: "Another declared workstream", kind: "workstream", members: ["deep-research"] });
    await route.fulfill({ response, json: data });
  });
  await page.goto("/workspace/#/?view=board&item=deep-research");
  const locations = page.getByRole("navigation", { name: "Workspace locations" });
  await expect(locations.locator("ol")).toHaveCount(2);
  await expect(locations).toContainText("Synthetic · knowledge workspace");
  await expect(locations).toContainText("Another declared workstream");
  await locations.getByRole("button", { name: "Paused supporting exploration", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("heading", { level: 2 })).toHaveText("Paused supporting exploration");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("region", { name: "Board", exact: true })).toBeVisible();
  const savedExpansion = await page.evaluate(() => localStorage.getItem("observatory:./data/:expanded"));
  await page.locator(".board-card").filter({ hasText: "Nested source experiment" }).click();
  await page.getByRole("button", { name: /Reveal in Overview/ }).focus();
  await page.keyboard.press("Enter");
  const record = page.locator(".record-button").filter({ hasText: "Nested source experiment" });
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(record).toHaveCount(2);
  await expect(record.first()).toBeFocused();
  await expect(record.first()).toHaveAttribute("aria-current", "location");
  await page.reload();
  await expect(record.first()).toBeFocused();
  expect(await page.evaluate(() => localStorage.getItem("observatory:./data/:expanded"))).toBe(savedExpansion);
  await page.getByRole("button", { name: "End reveal", exact: true }).click();
  await expect(record).toHaveCount(0);
  await expect(page.getByRole("searchbox")).toBeFocused();
  await expect(page.getByRole("button", { name: "Expand Synthetic · knowledge workspace", exact: true })).toHaveAttribute(
    "aria-expanded",
    "false",
  );
});

test("drawer reveal qualifies records outside filters and survives reload and browser history", async ({ page }) => {
  await page.goto("/workspace/#/?focus=plan&q=checkpoint&item=research");
  await expect(page.getByRole("dialog")).toContainText("Undated research");
  await page.getByRole("button", { name: /Reveal in Overview/ }).click();
  const research = page.locator(".record-button").filter({ hasText: "Undated research" });
  await expect(research).toBeFocused();
  await expect(page.locator(".reveal-notice")).toContainText("Outside your current filters");
  await expect(page.getByRole("button", { name: /^Planning \d/ })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("searchbox")).toHaveValue("checkpoint");
  await expect(page.locator(".workspace-toolbar")).toContainText("1 of 5 records");
  await expect(page.locator(".workstream-row.selected")).toHaveCSS("background-color", "rgb(238, 245, 255)");
  const checkpoint = page.locator(".record-button").filter({ hasText: "Planned checkpoint" });
  await checkpoint.click();
  await expect(page.getByRole("dialog").getByRole("heading", { level: 2 })).toHaveText("Planned checkpoint");
  await page.keyboard.press("Escape");
  await expect(checkpoint).toBeFocused();
  await page.reload();
  await expect(research).toBeFocused();
  await page.getByRole("button", { name: "End reveal", exact: true }).click();
  await expect(research).toHaveCount(0);
  await expect(page.getByRole("searchbox")).toBeFocused();
  await page.goBack();
  await expect(research).toBeFocused();
  await page.getByRole("button", { name: "Board", exact: true }).click();
  await expect(page.locator(".reveal-notice")).toHaveCount(0);
  await expect(page.locator(".board-card")).toHaveCount(1);
  await expect(page.locator(".board-card")).toContainText("Planned checkpoint");
  await page.goBack();
  await expect(research).toBeFocused();
});

test("real Open Presence drawer locations retain declared and derived provenance", async ({ page }, testInfo) => {
  test.skip(!process.env.OBSERVSTORY_LIVE_DATA, "Set OBSERVSTORY_LIVE_DATA to captured public consumer inputs");
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/live/#/?view=board&focus=research&item=research-pdf-history-claims");
  let locations = page.getByRole("navigation", { name: "Workspace locations" });
  await expect(locations).toContainText("PDF history · optional supporting module");
  await expect(locations).toContainText("Declared workspace");
  await expect(page.getByRole("dialog").getByRole("link").first()).toHaveAttribute(
    "href",
    /https:\/\/github.com\/blackmath88\/baselhack26-open-presence\/blob\//,
  );
  await page.screenshot({ path: testInfo.outputPath("open-presence-membership-detail.png") });
  await page.getByRole("button", { name: /Reveal in Overview/ }).click();
  await expect(page.locator(".record-button").filter({ hasText: "Claim ledger and verification queue" })).toBeFocused();
  await page.getByRole("button", { name: /^Implementation \d/ }).click();
  await page.getByRole("button", { name: "Board", exact: true }).click();
  const artifact = page
    .locator(".board-card")
    .filter({ hasText: /Observed / })
    .first();
  const title = (await artifact.locator("strong").textContent()) ?? "";
  await artifact.click();
  locations = page.getByRole("navigation", { name: "Workspace locations" });
  await expect(locations).toContainText("Repository implementation");
  await expect(locations).toContainText("Derived area grouping");
  await expect(locations).toContainText("Observed");
  await page.getByRole("button", { name: /Reveal in Overview/ }).click();
  await expect(page.locator(".record-button").filter({ hasText: title }).first()).toBeFocused();
  await page.screenshot({ path: testInfo.outputPath("open-presence-revealed-artifact.png"), fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});
