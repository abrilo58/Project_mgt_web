import { expect, test, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/login/");

  await page.fill("#username", "user");
  await page.fill("#password", "password");
  await page.click('button[type="submit"]');
  await page.waitForURL((url) => !url.pathname.includes("login"));
}

// --- Auth ---

test.describe.serial("kanban app", () => {
  test("unauthenticated visit to / redirects to /login", async ({ page }) => {
  await page.goto("/");
  await page.waitForURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });

  test("wrong credentials show an error", async ({ page }) => {
  await page.goto("/login/");

  await page.fill("#username", "user");
  await page.fill("#password", "wrong");
  await page.click('button[type="submit"]');
  await expect(page.getByRole("alert").filter({ hasText: /invalid/i })).toBeVisible();
  });

  test("correct credentials show the kanban board", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  });

  test("sign out returns to login page", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: /sign out/i }).click();
  await page.waitForURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  });

  // --- Kanban (requires auth) ---

  test("loads the kanban board", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
  });

  test("adds a card to a column", async ({ page }) => {
  await login(page);
  const title = `Playwright card ${Date.now()}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(title);
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: "Add card", exact: true }).click();
  await expect(firstColumn.getByText(title)).toBeVisible();
  });

  test("added card persists after reload", async ({ page }) => {
  await login(page);
  const title = `Persist card ${Date.now()}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await expect(firstColumn).toBeVisible();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(title);
  await firstColumn.getByRole("button", { name: "Add card", exact: true }).click();
  await expect(page.getByText(title)).toBeVisible();
  await page.reload({ waitUntil: "load" });
  await expect(page.locator('[data-testid^="column-"]').first()).toBeVisible({
    timeout: 20_000,
  });
  await expect(page.getByText(title)).toBeVisible({ timeout: 20_000 });
  });

  test("renamed column persists after reload", async ({ page }) => {
  await login(page);
  const col = page.locator('[data-testid^="column-"]').first();
  await expect(col).toBeVisible();
  const input = col.getByLabel("Column title");
  await input.fill("Icebox");
  await input.blur();
  await page.reload();
  await expect(page.locator('[data-testid^="column-"]').first()).toBeVisible();
  const colAfter = page.locator('[data-testid^="column-"]').first();
  await expect(colAfter.getByLabel("Column title")).toHaveValue("Icebox");
  });

  test("deleted card stays gone after reload", async ({ page }) => {
  await login(page);
  const title = `To delete ${Date.now()}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await expect(firstColumn).toBeVisible();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(title);
  await firstColumn.getByRole("button", { name: "Add card", exact: true }).click();
  await expect(page.getByText(title)).toBeVisible();
  await firstColumn
    .getByRole("button", { name: `Delete ${title}`, exact: true })
    .click();
  await expect(page.getByText(title)).not.toBeVisible();
  await page.reload();
  await expect(page.locator('[data-testid^="column-"]').first()).toBeVisible();
  await expect(page.getByText(title)).not.toBeVisible();
  });

  test("moved card persists in target column after reload", async ({ page }) => {
  await login(page);
  const title = `Drag me ${Date.now()}`;
  const backlog = page.locator('[data-testid^="column-"]').first();
  const review = page.locator('[data-testid^="column-"]').nth(3);
  await expect(backlog).toBeVisible();
  await expect(review).toBeVisible();
  await backlog.getByRole("button", { name: /add a card/i }).click();
  await backlog.getByPlaceholder("Card title").fill(title);
  await backlog.getByRole("button", { name: "Add card", exact: true }).click();
  const card = page
    .locator('[data-testid^="card-"]')
    .filter({ hasText: title })
    .first();
  await expect(card).toBeVisible();
  const cardBox = await card.boundingBox();
  const columnBox = await review.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }
  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(review.getByText(title)).toBeVisible();
  await page.reload();
  await expect(page.locator('[data-testid^="column-"]').nth(3)).toBeVisible();
  await expect(
    page.locator('[data-testid^="column-"]').nth(3).getByText(title)
  ).toBeVisible();
  });

  // --- AI chat (live OpenRouter; skip in CI without OPENROUTER_API_KEY) ---

  test("AI sidebar: send message and see assistant reply", async ({ page }) => {
    test.skip(!process.env.OPENROUTER_API_KEY, "OPENROUTER_API_KEY not set");
    test.setTimeout(120_000);
    await login(page);
    await page.getByTestId("ai-chat-toggle").click();
    await page
      .getByTestId("ai-chat-input")
      .fill("Reply with a single word only: ACK");
    await page.getByTestId("ai-chat-send").click();
    const assistant = page
      .getByTestId("ai-chat-messages")
      .getByTestId("ai-chat-msg-assistant")
      .last();
    await expect(assistant).toBeVisible({ timeout: 120_000 });
    await expect(assistant).toContainText(/ACK/i);
  });

  test("AI sidebar: create card on board without reload", async ({ page }) => {
    test.skip(!process.env.OPENROUTER_API_KEY, "OPENROUTER_API_KEY not set");
    test.setTimeout(120_000);
    await login(page);
    const title = `AI E2E ${Date.now()}`;
    const backlog = page.locator('[data-testid^="column-"]').first();
    await page.getByTestId("ai-chat-toggle").click();
    await page
      .getByTestId("ai-chat-input")
      .fill(
        `Add exactly one card to the Backlog column with title "${title}" (use board_update.cards_to_create).`
      );
    await page.getByTestId("ai-chat-send").click();
    await expect(backlog.getByText(title)).toBeVisible({ timeout: 120_000 });
  });

  test("AI sidebar: move card between columns without reload", async ({
    page,
  }) => {
    test.skip(!process.env.OPENROUTER_API_KEY, "OPENROUTER_API_KEY not set");
    test.setTimeout(120_000);
    await login(page);
    const title = `AI move ${Date.now()}`;
    const backlog = page.locator('[data-testid^="column-"]').first();
    const discovery = page.locator('[data-testid^="column-"]').nth(1);
    await backlog.getByRole("button", { name: /add a card/i }).click();
    await backlog.getByPlaceholder("Card title").fill(title);
    await backlog.getByRole("button", { name: "Add card", exact: true }).click();
    await expect(backlog.getByText(title)).toBeVisible();

    await page.getByTestId("ai-chat-toggle").click();
    await page
      .getByTestId("ai-chat-input")
      .fill(
        `Move the card titled "${title}" from Backlog to Discovery using board_update.cards_to_move (position 0).`
      );
    await page.getByTestId("ai-chat-send").click();
    await expect(discovery.getByText(title)).toBeVisible({ timeout: 120_000 });
  });

  test("AI sidebar: conversation shows multiple user messages", async ({
    page,
  }) => {
    test.skip(!process.env.OPENROUTER_API_KEY, "OPENROUTER_API_KEY not set");
    test.setTimeout(180_000);
    await login(page);
    await page.getByTestId("ai-chat-toggle").click();
    await page.getByTestId("ai-chat-input").fill("Say hi in one word.");
    await page.getByTestId("ai-chat-send").click();
    await expect(
      page.getByTestId("ai-chat-messages").getByTestId("ai-chat-msg-assistant").last()
    ).toBeVisible({ timeout: 120_000 });
    await page.getByTestId("ai-chat-input").fill("Say bye in one word.");
    await page.getByTestId("ai-chat-send").click();
    await expect(
      page.getByTestId("ai-chat-messages").getByTestId("ai-chat-msg-user")
    ).toHaveCount(2);
    await expect(
      page.getByTestId("ai-chat-messages").getByTestId("ai-chat-msg-assistant").last()
    ).toBeVisible({ timeout: 120_000 });
  });

});
