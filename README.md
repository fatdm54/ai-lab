# 🤖 AI Lab — AI赚钱实验室

> 用 AI 自动化赚钱的真实实验记录
> 
> **Status:** 🟢 Active | **Phase:** 0 - Foundation | **Revenue:** $0 → $5,000/月

---

## 🎯 定位

**一句话：** 用免费 AI API + 自动化系统，从零搭建可持续的被动收入来源。

### 核心理念

- 🆓 **全部免费** — 只用免费 API 和开源工具
- 🤖 **全自动化** — 内容生成、发布、分析全部自动
- 📊 **数据驱动** — 每个决策都有数据支撑
- 🔍 **透明公开** — 所有收入数据实时公开

---

## 📐 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Lab Core System                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Content  │  │ Platform │  │Analytics │  │Scheduler │   │
│  │Generator │→ │Publisher │→ │ Tracker  │← │  Engine  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↑              │              │              │         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   API    │  │    X     │  │ Telegram │  │ YouTube  │   │
│  │ Gateway  │  │ Twitter  │  │   Bot    │  │ Channel  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 6-Phase Roadmap

| Phase | Name | Timeline | Goal | Status |
|-------|------|----------|------|--------|
| **0** | 基础设施 | Day 1-3 | API 配置 + Pipeline | 🟡 In Progress |
| **1** | X/Twitter | Week 1-2 | 500 粉丝 + 自动发推 | ⬜ Not Started |
| **2** | Telegram Bot | Week 2-4 | 100 用户 + $250/月 | ⬜ Not Started |
| **3** | YouTube | Week 4-8 | 1000 订阅 + $500/月 | ⬜ Not Started |
| **4** | 规模化 | Month 2-4 | 5000 粉丝 + $2,000/月 | ⬜ Not Started |
| **5** | 变现 | Month 4-6 | 20000 粉丝 + $5,000/月 | ⬜ Not Started |

### Phase 之间的关系

```
Phase 1 (X) ──引流──→ Phase 2 (Telegram)
    │                      │
    └──预告──→ Phase 3 (YouTube)
                   │
                   └──内容复用──→ Phase 4 (规模化)
                                      │
                                      └──流量变现──→ Phase 5 (收入)
```

---

## 🛠 Tech Stack

- **Language:** Python 3.11+
- **AI APIs:** Google Gemini 2.5 Flash, Groq, Mistral (all free tier)
- **Platforms:** X/Twitter API, Telegram Bot API, YouTube Data API
- **Infrastructure:** Linux server (24/7), cron, systemd
- **Database:** SQLite (lightweight, no setup)
- **Monitoring:** Custom analytics + Telegram alerts

---

## 📁 Project Structure

```
ai-lab/
├── config/                 # Configuration
│   ├── settings.py         # Global settings
│   └── secrets.example.json # API key template
├── core/                   # Core modules
│   ├── api_gateway.py      # Multi-provider API with key rotation
│   ├── content_generator.py # Topic → multi-platform content
│   └── analytics.py        # Data tracking
├── platforms/              # Platform integrations
│   ├── x_twitter.py        # X/Twitter publisher
│   ├── telegram.py         # Telegram bot
│   └── youtube.py          # YouTube publisher
├── scheduler/              # Task scheduling
│   ├── queue.py            # Content queue
│   └── cron.py             # Cron job manager
├── templates/              # Content templates
│   ├── x_threads/          # X thread templates
│   ├── telegram/           # Telegram post templates
│   └── youtube/            # YouTube script templates
├── data/                   # Data storage (gitignored)
├── logs/                   # Logs (gitignored)
├── tests/                  # Test suite
├── docs/                   # Documentation
│   └── plans/              # Implementation plans
├── scripts/                # Utility scripts
└── main.py                 # Entry point
```

---

## 🏃 Quick Start

```bash
# Clone the repo
git clone https://github.com/fatdm54/ai-lab.git
cd ai-lab

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure API keys
cp config/secrets.example.json config/secrets.json
# Edit config/secrets.json with your keys

# Run the system
python main.py --status
```

---

## 📊 Revenue Dashboard

| Source | Month 1 | Month 3 | Month 6 |
|--------|---------|---------|---------|
| YouTube Ads | $0 | $500 | $3,000 |
| Telegram Bot | $0 | $250 | $1,000 |
| Affiliate | $0 | $100 | $500 |
| Brand Deals | $0 | $0 | $500 |
| **Total** | **$0** | **$850** | **$5,000** |

> 💡 All revenue data is transparent and updated weekly in `/docs/revenue/`

---

## 🤝 Contributing

This is a solo experiment, but feel free to:
- Open issues for suggestions
- Fork and build your own version
- Share your results

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- [Roadmap](docs/plans/roadmap.md)
- [Revenue Reports](docs/revenue/)
- [API Configuration](config/)

---

> **Built with ❤️ and free AI APIs**
