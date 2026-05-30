# AI Interview Training Platform V4 Local Max

这是一个适合本地电脑运行的 AI 应用开发高含金量项目。

它不是企业生产环境，但已经包含 AI 应用开发面试里最关键的工程能力展示。

## 核心能力

- FastAPI 后端
- JWT 登录鉴权
- SQLite 用户与历史数据库
- Chroma 持久化向量库
- SentenceTransformer Embedding
- RAG Top-K 粗召回
- 简化 Rerank
- Prompt 版本管理
- Stateful Agent Session
- 面试评分 Agent
- 基于历史的追问 Agent
- 弱项分析
- 知识库上传
- 检索评测接口
- LLM 调用缓存
- 本地日志
- 简易前端页面
- Docker 配置

## 它和普通 RAG Demo 的区别

普通 Demo：

```text
用户问题 -> 向量检索 -> LLM回答
```

本项目：

```text
用户注册登录
-> 选择目标岗位
-> RAG检索岗位知识
-> Rerank筛选上下文
-> 生成第一题
-> 创建有状态Session
-> 用户回答
-> 评分Agent
-> 历史驱动追问Agent
-> 保存每轮面试
-> 弱项分析
-> 检索评测
-> 日志和缓存
```

## 启动

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

```text
frontend/index.html
```

## 简历写法

AI Interview Training Platform  
基于 FastAPI + Chroma + SentenceTransformer + DeepSeek API 构建 AI 面试训练平台，实现 JWT 登录、岗位定制面试、RAG 检索、简化 Rerank、有状态 Agent Session、回答评分、历史驱动追问、训练历史保存、弱项分析、Prompt 版本管理与检索评测体系。

## 面试可讲点

1. 为什么要 Embedding
2. Chroma 如何做语义检索
3. 为什么需要 Rerank
4. RAG 如何降低幻觉
5. System Prompt 如何约束回答
6. Agent Session 如何保存状态
7. 为什么评分和追问要结合历史 turns
8. 如何设计检索评测 hit rate
9. 为什么需要 Prompt 版本管理
10. 为什么需要缓存和日志

## 工程化升级亮点

- 使用 pytest + FastAPI TestClient 覆盖注册、登录、JWT 鉴权、面试 Session、多轮回答、RAG 问答和健康检查。
- 针对重复注册、非法邮箱、超长密码、未登录访问、错误 token、空回答等异常输入设计边界测试。
- 检索评估接口返回 Hit Rate、Recall@1、Recall@3、Recall@5 和平均相似度，便于量化 RAG 召回质量。
- LLM 输出支持前端 JSON 解析兜底，字段缺失时不崩溃，原始响应保留在 Debug 面板。
- 后端增加请求日志中间件，记录接口路径、状态码、耗时和异常类型，便于线上排查。
- 配置 GitHub Actions CI，在 push / PR 时运行后端编译和 pytest。

## 本地前端访问

不要直接双击 `frontend/index.html` 作为主要测试方式，`file://` 可能触发浏览器安全策略。推荐使用：

```powershell
py -m http.server 4173 --bind 127.0.0.1 --directory frontend
```

然后打开：

```text
http://127.0.0.1:4173/
```
