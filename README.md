# 小暖 AI 伴侣

基于 LangGraph 多 Agent 架构的 AI 情感陪伴应用。微信小程序 + FastAPI 后端。

## 功能

- **四角色女友**: 甜妹小糖 / 御姐若琳 / 清纯清禾 / 辣妹辣辣
- **亮亮导师**: 专业成长导师，专属复刻音色
- **情感感知**: 识别用户情绪（开心/难过/生气/焦虑）+ 意图（倾诉/求助/闲聊）
- **语音合成**: CosyVoice 实时 TTS，LLM 智能判断是否出声
- **RAG 知识库**: 文档上传 → 自动分块 → ChromaDB → 对话中自然引用
- **对话记忆**: MySQL 持久化，历史对话可回溯
- **管理后台**: 仪表盘 / 知识库管理 / 用户管理 / 对话记录 / 系统配置

## 技术栈

```
后端:    Python FastAPI + LangChain + LangGraph
LLM:     阿里云百炼 (qwen-plus)
TTS:     百炼 CosyVoice (cosyvoice-v3-flash)
向量库:   ChromaDB
数据库:   MySQL 8.0
前端:    微信小程序
部署:    Docker Compose
```

## 项目结构

```
├── backend/
│   ├── agents/          LangGraph Agent 节点
│   ├── api/routes/      REST + WebSocket
│   ├── core/            LLM / Embedding / Vector Store
│   ├── db/              数据库连接
│   ├── models/          ORM 实体
│   ├── services/        业务服务
│   └── utils/           工具
├── mini-program/        微信小程序
├── admin/               管理后台前端
├── sql/                 建表脚本
└── docker-compose.yml   容器编排
```

## 快速启动

```bash
# 1. 安装依赖
uv sync

# 2. 配置 .env
cp .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY

# 3. MySQL 建库
mysql -u root -p < sql/init.sql

# 4. 启动
uv run uvicorn backend.main:app --reload --port 8000

# 5. 打开管理后台
# http://localhost:8000/admin/  (admin / admin123)
```

## Docker 部署

```bash
export DASHSCOPE_API_KEY=sk-xxx
docker-compose up -d
```

## Agent 工作流

```
perception → memory → persona → knowledge → response → voice_decision
  (情绪+意图) (画像)   (人设)    (ChromaDB)   (流式回复)   (LLM判断出声)
```

## License

MIT
