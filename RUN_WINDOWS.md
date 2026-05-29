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

直接打开：

```text
frontend/index.html
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
