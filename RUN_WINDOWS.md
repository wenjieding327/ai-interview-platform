# Windows 本地运行

## Backend

```powershell
cd backend
copy .env.example .env
notepad .env
py -m pip install -r requirements.txt
alembic upgrade head
py -m uvicorn main:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

## Frontend

推荐用本地 HTTP server 打开，不要把 `file://` 作为主要测试方式。

```powershell
cd ..
py -m http.server 4173 --bind 127.0.0.1 --directory frontend
```

然后访问：

```text
http://127.0.0.1:4173/
```

Pitch 页面：

```text
http://127.0.0.1:4173/pitch.html
```

## 推荐测试顺序

1. `/auth/register`
2. `/auth/login`
3. Swagger 右上角 Authorize，输入 `Bearer <token>`
4. `/interview/start`
5. `/interview/session_step`
6. `/interview/session/{session_id}`
7. `/eval/retrieval`
8. `/report/weakness`
9. `/admin/logs`
10. `/agent/tools`
11. `/agent/tool-call`

## Playwright E2E

```powershell
npm install
npx playwright install chromium
npm run e2e
```

默认会测试线上 Vercel 地址。要测试本地前端：

```powershell
$env:E2E_BASE_URL="http://127.0.0.1:4173"
npm run e2e
```

## PostgreSQL

本地默认 SQLite，方便快速运行。生产环境推荐 PostgreSQL：

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB_NAME
```

迁移命令：

```powershell
cd backend
alembic upgrade head
```
