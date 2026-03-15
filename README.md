# 🤖 KeyforAgents Automation Engine

> The unified AI automation engine powering [KeyforAgents.com](https://keyforagents.com) — Australia's leading AI agent marketplace for real estate agencies and B2B businesses.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

---

## 🚀 What This Is

This repo is the **master automation engine** that combines all KeyforAgents systems into one pipeline:

- 🧠 **Manus Agent Core** — autonomous AI planning, memory, multi-step reasoning
- 📈 **Sales Automation** — hands-free lead gen, outreach, and campaign management
- 💬 **Telegram Bot** — real-time agent communication and client notifications
- 🔗 **n8n Workflows** — no-code automation pipelines connecting all services
- 💳 **Stripe/PayPal Billing** — subscription management and payment processing
- 🏠 **AI Lead Generation** — real estate agency targeting across Australia
- 🌐 **API Gateway** — FastAPI backend orchestrating all agents

---

## 🏗️ Architecture

```
keyforagents-automation-engine/
├── agents/                  # Manus agent modules
│   ├── lead_agent.py        # Real estate lead generation
│   ├── sales_agent.py       # Automated outreach
│   └── telegram_agent.py    # Telegram communication
├── api/                     # FastAPI gateway
│   ├── main.py
│   ├── routes/
│   └── middleware/
├── billing/                 # Stripe + PayPal integration
│   ├── stripe_handler.py
│   └── paypal_handler.py
├── workflows/               # n8n workflow JSON exports
├── scrapers/                # Web scraping modules
├── config/                  # Environment and settings
├── tests/                   # Test suite
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

```bash
# Clone the repo
git clone https://github.com/helpinghands3631-bot/keyforagents-automation-engine.git
cd keyforagents-automation-engine

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env

# Run the API gateway
python api/main.py
```

---

## 🔑 Environment Variables

```env
# AI / LLM
GROK_API_KEY=your_grok_key
OPENAI_API_KEY=your_openai_key

# Billing
STRIPE_SECRET_KEY=your_stripe_key
PAYPAL_CLIENT_ID=your_paypal_id
PAYPAL_SECRET=your_paypal_secret

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Database
DATABASE_URL=postgresql://user:pass@localhost/keyforagents

# n8n
N8N_WEBHOOK_URL=your_n8n_webhook
```

---

## 🤝 Related Repos

| Repo | Description |
|------|-------------|
| [manus-agent-core](https://github.com/helpinghands3631-bot/manus-agent-core) | Base agent framework |
| [manus-sales-automation](https://github.com/helpinghands3631-bot/manus-sales-automation) | Sales pipeline automation |
| [re-lead-doctor-app](https://github.com/helpinghands3631-bot/re-lead-doctor-app) | Real estate lead SaaS frontend |
| [re-lead-doctor-api](https://github.com/helpinghands3631-bot/re-lead-doctor-api) | Real estate lead SaaS backend |
| [manus-telegram-agent](https://github.com/helpinghands3631-bot/manus-telegram-agent) | Telegram bot agent |
| [creator-app](https://github.com/helpinghands3631-bot/creator-app) | 3-copilot creator platform |

---

## 🌏 Built for Australia

This engine is designed specifically for the **Australian real estate and B2B market**:
- Suburb-level SEO targeting
- AUS timezone scheduling
- Stripe AUD payment support
- Integration with Australian real estate portals

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

**Made with ❤️ by [Helping Hands](https://helpinghands.com.au) | ABN 65 681 861 276 | Shepparton, VIC, Australia**
