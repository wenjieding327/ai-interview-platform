const { spawn } = require("node:child_process");
const path = require("node:path");
const os = require("node:os");
const fs = require("node:fs");

const backend = process.argv[2] === "backend";
const root = path.resolve(__dirname, "..");
const storage = fs.mkdtempSync(path.join(os.tmpdir(), "interview-e2e-"));
const python = process.env.PYTHON || (process.platform === "win32" ? "py" : "python");
const prefix = python === "py" ? ["-3.11"] : [];
const args = backend
  ? ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8005"]
  : ["-m", "http.server", "4175", "--bind", "127.0.0.1", "--directory", "frontend"];
const child = spawn(python, [...prefix, ...args], {
  cwd: backend ? path.join(root, "backend") : root,
  stdio: "inherit", windowsHide: true,
  env: { ...process.env, PYTHONUTF8: "1", USE_FAKE_LLM: "true", RETRIEVAL_MODE: "lexical",
    DATABASE_URL: "sqlite:///" + path.join(storage, "test.db").replaceAll("\\", "/"),
    LOG_PATH: path.join(storage, "events.jsonl"), RUN_DB_MIGRATIONS: "true", JWT_SECRET_KEY: "e2e-only-secret" },
});
child.on("exit", code => process.exit(code || 0));
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => { child.kill(); });
