const { test, expect } = require("@playwright/test");

async function signIn(page) {
  await page.goto("/");
  if (!process.env.E2E_BASE_URL || process.env.E2E_API_URL) {
    await page.locator("#api").fill(process.env.E2E_API_URL || "http://127.0.0.1:8005");
    await page.locator("#api").press("Tab");
  }
  const email = `e2e+${Date.now()}@example.com`;
  await page.locator("#email").fill(email);
  await page.locator("#pwd").fill("E2ePass12345");
  await page.locator("#registerBtn").click();
  await expect(page.locator("#chat")).toContainText("注册成功");
  await page.locator("#loginBtn").click();
  await expect(page.locator("#startBtn")).toBeEnabled();
  await page.locator("#startBtn").click();
  await expect(page.locator("#sid")).not.toHaveText("--");
  await expect(page.locator("#answer")).toBeEnabled();
  return email;
}

test("register, six unanswered rounds, zero-score summary, and restore after reload", async ({ page }) => {
  test.setTimeout(180000);
  await signIn(page);
  const questions = [];
  for (let turn = 1; turn <= 6; turn++) {
    const question = await page.locator(".next-body").last().innerText();
    expect(questions).not.toContain(question);
    questions.push(question);
    await page.locator("#answer").fill("不知道");
    await page.locator("#sendBtn").click();
    await expect(page.locator("#turn")).toHaveText(String(turn));
    await expect(page.locator("#score")).toHaveText("0");
  }
  await expect(page.locator(".final-card")).toContainText("0 / 100");
  await expect(page.locator("#answer")).toBeDisabled();
  await expect(page.locator("#sendBtn")).toBeDisabled();
  await expect(page.locator("#chat")).not.toContainText('"score"');
  await expect(page.locator("#reviews .review-item")).toHaveCount(6);
  await expect(page.locator("#chat").getByText("已记录。本轮评分和优缺点已放到右侧 Question Reviews。")).toHaveCount(1);
  await page.reload();
  await page.locator("#pwd").fill("E2ePass12345");
  await page.locator("#loginBtn").click();
  await expect(page.locator(".final-card")).toContainText("0 / 100");
  await expect(page.locator("#reviews .review-item")).toHaveCount(6);
  const download = page.waitForEvent("download");
  await page.locator("#exportBtn").click();
  expect((await download).suggestedFilename()).toMatch(/interview-\d+-review.txt/);
});

test("lost response retries without duplicate turns; failed finish stays retryable", async ({ page }) => {
  await signIn(page);
  let interrupted = false;
  await page.route("**/interview/session_step", async route => {
    if (!interrupted) {
      interrupted = true;
      await route.fetch();
      await route.abort("connectionfailed");
    } else await route.continue();
  });
  await page.locator("#answer").fill("不知道");
  await page.locator("#sendBtn").click();
  await expect(page.locator("#chat")).toContainText("提交失败");
  await expect(page.locator("#answer")).toHaveValue("不知道");
  await page.locator("#sendBtn").click();
  await expect(page.locator("#turn")).toHaveText("1");
  await expect(page.locator("#reviews .review-item")).toHaveCount(1);
  await page.route("**/finish", route => route.abort("connectionfailed"));
  await page.locator("#finishBtn").click();
  await expect(page.locator("#chat")).toContainText("结束失败");
  await expect(page.locator(".final-card")).toHaveCount(0);
  await expect(page.locator("#finishBtn")).toBeEnabled();
  await page.unroute("**/finish");
  await page.locator("#finishBtn").click();
  await expect(page.locator(".final-card")).toContainText("0 / 100");
});

test("active draft and progress recover after re-login; RAG and retrieval tools work", async ({ page }) => {
  await signIn(page);
  await page.locator("#answer").fill("不知道");
  await page.locator("#sendBtn").click();
  await expect(page.locator("#turn")).toHaveText("1");
  await page.locator("#answer").fill("尚未发送的回答草稿");
  await page.reload();
  await page.locator("#pwd").fill("E2ePass12345");
  await page.locator("#loginBtn").click();
  await expect(page.locator("#answer")).toHaveValue("尚未发送的回答草稿");
  await expect(page.locator("#turn")).toHaveText("1");
  await page.locator("#answer").fill("什么是 RAG？");
  await page.getByRole("button", { name: "Ask RAG", exact: true }).click();
  await expect(page.locator("#chat")).toContainText("RAG 回答");
  await page.getByRole("button", { name: "Retrieval Eval", exact: true }).click();
  await expect(page.locator("#chat")).toContainText("检索评估完成");
  await page.getByRole("button", { name: "Agent Router", exact: true }).click();
  await expect(page.locator("#chat")).toContainText("选择工具");
});

test("mobile layout contains controls without horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/mobile-interview.png", fullPage: true });
});

test("expired login preserves draft and allows re-login without losing the session", async ({ page }) => {
  await signIn(page);
  await page.route("**/interview/session_step", route => route.fulfill({
    status: 401, contentType: "application/json", body: JSON.stringify({ detail: "Invalid authentication credentials" })
  }));
  await page.locator("#answer").fill("不知道");
  await page.locator("#sendBtn").click();
  await expect(page.locator("#chat")).toContainText("登录状态失效");
  await expect(page.locator("#answer")).toHaveValue("不知道");
  await page.unroute("**/interview/session_step");
  await page.locator("#loginBtn").click();
  await expect(page.locator("#answer")).toBeEnabled();
  await expect(page.locator("#answer")).toHaveValue("不知道");
  await page.locator("#sendBtn").click();
  await expect(page.locator("#turn")).toHaveText("1");
});
