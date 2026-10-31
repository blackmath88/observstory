import { expect, type Page, test } from "@playwright/test";

/** Collect console errors and uncaught exceptions for the whole test. The browser's own log line
 *  for a 404 is expected when an optional input (knowledge.json) is not published; the page
 *  reports that state itself, so it is not counted as an error. */
function trackErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && !m.text().startsWith("Failed to load resource") && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

test("opens a snapshot under a project subpath and shows the repository", async ({ page }) => {
  const errors = trackErrors(page);
  await page.goto("/hackathon/");
  await expect(page.locator(".repo-title")).toContainText("northstar/voice-notes");
  await expect(page.getByLabel("Project summary")).toContainText("in flight");
  await expect(page.getByRole("heading", { name: "Lanes" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("direct entry and reload on a hash route work without a server fallback", async ({ page }) => {
  const errors = trackErrors(page);
  await page.goto("/hackathon/#/sources");
  await expect(page.getByRole("heading", { name: "Data sources" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Data sources" })).toBeVisible();
  await expect(page.getByText("Not published (optional)")).toBeVisible();
  expect(errors).toEqual([]);
});

test("broken inputs fail visibly and never render as zero", async ({ page }) => {
  await page.goto("/broken/");
  await expect(page.getByRole("alert")).toContainText("Activity is unavailable");
  await expect(page.getByLabel("Project summary")).toHaveCount(0);
  await page
    .getByRole("link", { name: /Data sources/ })
    .first()
    .click();
  await expect(page.getByText(/Unsupported version: found observstory.snapshot\/v9/)).toBeVisible();
  await expect(page.getByText("Not valid JSON")).toBeVisible();
});

test("a quiet project says so instead of looking broken", async ({ page }) => {
  await page.goto("/quiet/");
  await expect(page.getByText("Nothing needs a conversation right now.")).toBeVisible();
});

test("tabs are keyboard reachable with a visible current page", async ({ page }) => {
  await page.goto("/hackathon/");
  const sources = page.getByRole("link", { name: /Data sources/ });
  await sources.focus();
  await page.keyboard.press("Enter");
  await expect(sources).toHaveAttribute("aria-current", "page");
});
