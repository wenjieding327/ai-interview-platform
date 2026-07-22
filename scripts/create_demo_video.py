from pathlib import Path
import textwrap

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "demo"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "ai_interview_platform_2min_demo.mp4"

W, H = 1280, 720
FPS = 1


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


TITLE = font(48, True)
SUBTITLE = font(28, False)
BODY = font(27, False)
SMALL = font(22, False)


SLIDES = [
    ("AI Interview Training Platform", "FastAPI + RAG + Agent Router + Evaluation + Cloud Deployment",
     ["面向 AI 应用开发岗位的模拟面试平台", "不是普通聊天 UI，而是完整工程化 AI 应用", "在线演示：Vercel 前端 + Railway 后端"], 16),
    ("Product Flow", "从登录到多轮面试，再到综合评价",
     ["JWT 注册/登录，用户会话隔离", "Start Interview 创建 stateful session", "每轮回答保存为 turn，结束后生成综合评价"], 18),
    ("RAG Knowledge System", "让面试围绕真实 AI 应用能力展开",
     ["Chroma 向量库 + Embedding 检索", "Rerank 候选知识，再注入 Prompt", "支持上传 .txt 扩展知识库"], 18),
    ("Agent Tool Router", "一个可测试的 Tool Calling 风格智能体",
     ["Ask RAG：回答知识库问题", "Retrieval Eval：评估 Hit Rate 与 Recall@K", "Weakness Report / Logs：生成薄弱点与排障证据"], 20),
    ("Engineering Evidence", "让项目像正式工作，而不是截图 Demo",
     ["pytest + FastAPI TestClient 覆盖核心接口", "GitHub Actions 每次 push 自动测试", "Docker / Railway / Vercel 云端部署闭环"], 18),
    ("Why It Matters", "可用于求职、比赛、作品集和后续商业化",
     ["证明 LLM、RAG、Agent、Prompt、部署、测试都能落地", "下一步可扩展班级看板、PDF 报告、题库管理", "适合投 AI 应用开发实习/初级岗位"], 20),
    ("Live Demo Links", "Ready to show in an interview",
     ["Frontend: ai-interview-platform-taupe-chi.vercel.app", "Backend: selfless-rejoicing-production-4735.up.railway.app", "GitHub: wenjieding327/ai-interview-platform"], 10),
]


def draw_slide(slide, index: int):
    title, subtitle, bullets, _seconds = slide
    img = Image.new("RGB", (W, H), "#071018")
    draw = ImageDraw.Draw(img)

    for y in range(H):
        ratio = y / H
        draw.line([(0, y), (W, y)], fill=(int(7 + ratio * 9), int(16 + ratio * 18), int(24 + ratio * 28)))

    draw.rectangle([0, 0, W, 78], fill="#0d1726")
    draw.text((56, 24), "AI Interview Coach", fill="#9df3ff", font=SMALL)
    draw.text((W - 190, 24), f"{index + 1}/7", fill="#d7e4ff", font=SMALL)
    draw.text((72, 130), title, fill="#ffffff", font=TITLE)
    draw.text((75, 198), subtitle, fill="#7dd3fc", font=SUBTITLE)

    y = 300
    for bullet in bullets:
        draw.rounded_rectangle([78, y - 10, 1120, y + 58], radius=14, fill="#101c2f", outline="#1f3b5a")
        draw.ellipse([100, y + 10, 118, y + 28], fill="#4dd7df")
        lines = textwrap.wrap(bullet, width=42)
        draw.text((140, y + 3), "\n".join(lines), fill="#eef6ff", font=BODY, spacing=6)
        y += 96

    draw.line([(72, 640), (1208, 640)], fill="#203a52", width=2)
    draw.text((72, 662), "Generated from docs/demo materials", fill="#93a4b8", font=SMALL)
    return np.array(img)


def main():
    frames = []
    for index, slide in enumerate(SLIDES):
        frames.extend([draw_slide(slide, index)] * slide[3])
    imageio.mimsave(OUT_FILE, frames, fps=FPS, quality=8)
    print(OUT_FILE)


if __name__ == "__main__":
    main()
