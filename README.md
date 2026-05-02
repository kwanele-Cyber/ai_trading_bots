# Fundamental FX Bot (Forward Guidance)

A Python bot scaffold that runs **twice daily** and builds **forward-looking**
fundamental analysis for major/minor FX pairs.

## What it covers
- Central bank decisions framed by each bank's mandate/reaction function.
- Seasonality windows and macro flow patterns.
- Upcoming high-impact event risks.
- Geopolitical and tariff-related headlines.
- Major-bank narrative consensus/divergence.

The goal is to generate guidance on **future likely price drivers**, not simply
summarize data already released and priced.

It now uses a **persona LLM chain**: multiple specialist agents (central-bank,
geopolitical, flow/seasonality, and sell-side narrative) produce first-pass views
that are then synthesized by a chief strategist into a final trade memo.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
export FX_PAIRS="EURUSD,GBPUSD,USDJPY,AUDNZD"
python fundamental_fx_bot.py
```

Default schedule is **06:00 UTC** and **18:00 UTC** daily.

## Next integrations you should add
1. Central bank source ingestion (official speeches, minutes, decisions).
2. Economic calendar API + event surprise model.
3. Newswire source with relevance scoring for pair legs.
4. Major-bank research ingestion (licensed feeds).
5. Risk engine to convert guidance into position sizing/playbooks.
