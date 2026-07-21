# Windows 本地运行

```powershell
cd backend
copy .env.example .env
notepad .env
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload
```

打开：

```text
http://127.0.0.1:8000/docs
```

前端：

推荐用本地 HTTP server 打开，不要把 `file://` 作为主要测试方式：

```powershell
cd ..
py -m http.server 4173 --bind 127.0.0.1 --directory frontend
```

然后访问：

```text
http://127.0.0.1:4173/
```

## 推荐测试顺序

1. `/auth/register`
2. `/auth/login`
3. Swagger右上角 Authorize，输入 `Bearer <token>`
4. `/interview/start`
5. `/interview/session_step`
6. `/interview/session/{session_id}`
7. `/eval/retrieval`
8. `/report/weakness`
9. `/admin/logs`
10. `/agent/tools`
11. `/agent/tool-call`
