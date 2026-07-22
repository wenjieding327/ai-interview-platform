const { test, expect } = require("@playwright/test");

test("register, login, start interview, submit answer, and run agent tools", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("AI Interview Coach")).toBeVisible();

  const email = `e2e+${Date.now()}@example.com`;
  await page.locator("#email").fill(email);
  await page.locator("#pwd").fill("E2ePass12345");

  await page.getByRole("button", { name: "注册" }).click();
  await expect(page.getByText("注册成功")).toBeVisible();

  await page.getByRole("button", { name: "登录" }).click();
  await expect(page.getByText("登录成功")).toBeVisible();

  await page.getByRole("button", { name: "开始面试" }).click();
  await expect(page.getByText("下一问").or(page.getByText("Mock Interview Session"))).toBeVisible();
  await expect(page.locator("#sid")).not.toHaveText("--");

  await page.locator("#answer").fill(
    "我会将 AI 面试平台拆成前端、FastAPI 后端、RAG 检索服务和评估模块。后端用 JWT 保护接口，用 Chroma 存储向量，用 Recall@K 和 Hit Rate 评估召回质量，并把每轮回答保存到 session turns 中。"
  );
  await page.getByRole("button", { name: "发送" }).click();

  await expect(page.getByText("Question Reviews")).toBeVisible();
  await expect(page.locator("#turn")).toHaveText("1", { timeout: 45000 });
  await expect(page.getByText("第 1 轮")).toBeVisible();

  await page.locator("#answer").fill("请检查 RAG 检索评估，展示 Recall@K 和 Hit Rate");
  await page.getByRole("button", { name: "Agent Router" }).click();
  await expect(page.getByText("Agent Router")).toBeVisible({ timeout: 45000 });
  await expect(page.locator("#chat").getByText(/选择工具：\s*retrieval_eval/)).toBeVisible();

  await page.getByRole("button", { name: "Retrieval Eval" }).click();
  const retrievalCard = page.locator("#chat .bubble").filter({ hasText: "检索评估完成" });
  await expect(retrievalCard).toBeVisible({ timeout: 45000 });
  await expect(retrievalCard.getByText("Recall@3")).toBeVisible();
});
