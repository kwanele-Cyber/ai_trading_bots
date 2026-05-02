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

## System design: mini multi-agent market analyst

Below is a practical design for a mini agentic analyst that can output directional
**bias** for a provided symbol, FX pair, country, or ticker.

### 1) Product objective and output contract

**Input**
- `instrument_type`: `fx_pair | equity_ticker | commodity | country_index`
- `instrument`: e.g. `EURUSD`, `AAPL`, `XAUUSD`, `Japan`
- `horizon`: `intraday | 1-2w | 1-3m`
- `risk_profile`: `conservative | balanced | aggressive`

**Output**
- `bias`: `bullish | bearish | neutral`
- `confidence`: 0-100
- `key_drivers`: ranked list with short rationale
- `known_risks`: top invalidation conditions
- `next_events`: catalyst calendar affecting the view

### 2) High-level architecture

```text
Client/API
  -> Orchestrator Agent
      -> Data Router + Retrieval Layer
          -> Central Bank Agent
          -> Geopolitics Agent
          -> Macro News/Event Agent
          -> Seasonality/Flow Agent
          -> Cross-Asset Regime Agent
      -> Evidence Normalizer (shared schema)
      -> Weighting & Scoring Engine
      -> Chief Strategist Synthesizer
  -> Response API + Audit Log + Monitoring
```

### 3) Agent roles

#### A. Central Bank Mandate Agent
- Tracks inflation, labor, growth, and policy-communication tone relative to each
  bank's mandate/reaction function.
- Outputs policy stance and likely rate-path impulse for the target instrument.

#### B. Geopolitical Agent
- Scores conflict, sanctions, trade policy, election, and diplomatic headlines by
  market impact probability and persistence.
- Maps events to channels: growth shock, commodity shock, risk sentiment, and
  capital-flow stress.

#### C. Macro News/Event Agent
- Handles scheduled events (CPI, payrolls, GDP, PMIs, central-bank dates) and
  unscheduled breaking news.
- Computes event surprise direction vs consensus and relevance to instrument legs.

#### D. Seasonality/Flow Agent
- Learns month/week/day seasonal tendencies and periodic flow effects (tax,
  rebalancing, pension, corporate hedging windows).
- Flags whether current period historically supports or fades trend continuation.

#### E. Cross-Asset Regime Agent
- Classifies regime from rates, vol, credit spreads, commodities, and broad risk
  proxies to avoid single-factor overconfidence.
- Produces a regime label (risk-on/off, inflationary/disinflationary, liquidity
  loose/tight) and expected asset behavior.

### 4) Shared evidence schema (critical)

Every specialist must return a normalized object:

```json
{
  "agent": "central_bank",
  "direction": "bullish|bearish|neutral",
  "confidence": 0.0,
  "horizon": "1-2w",
  "impact_channels": ["rates", "growth", "risk"],
  "evidence": [
    {
      "claim": "ECB communication shifted less dovish",
      "source": "official_speech",
      "timestamp_utc": "2026-05-02T10:00:00Z",
      "strength": 0.73
    }
  ],
  "half_life_hours": 72,
  "risks": ["US data surprise re-prices Fed path"]
}
```

This schema enables deterministic ranking, conflict resolution, and auditability.

### 5) Orchestration and decision logic

1. **Instrument decomposition**
   - For FX, split into base/quote and compute relative scores.
   - For equities, map ticker to domicile, sector, and factor exposures.
2. **Agent query planning**
   - Pull only relevant sources/time windows per horizon.
3. **Independent agent inference**
   - Each specialist submits evidence object with confidence + half-life.
4. **Weighting engine**
   - Dynamic weights by horizon and regime (e.g., central-bank weight up for
     1-3m, event/news weight up for intraday).
5. **Conflict handling**
   - Penalize stale evidence and low-source-quality claims.
   - If strong disagreement, cap confidence and force neutral/low-conviction bias.
6. **Chief strategist synthesis**
   - Produces concise narrative, catalysts, invalidation, and final bias score.

### 6) Scoring model (simple but robust)

- Agent directional score: `s_i in [-1, 1]`
- Agent confidence: `c_i in [0, 1]`
- Recency decay: `d_i = exp(-age/half_life)`
- Source quality multiplier: `q_i in [0.5, 1.2]`
- Dynamic weight: `w_i`

Composite:

`final_score = sum(w_i * s_i * c_i * d_i * q_i) / sum(w_i)`

Map to bias:
- `> +0.2`: bullish
- `< -0.2`: bearish
- otherwise neutral

Confidence can be calibrated from agreement level + data freshness + backtested
hit-rate for current regime.

### 7) Data layer recommendations

- **Official / high-trust**: central bank statements, minutes, speeches,
  government releases, statistical agencies.
- **Market data**: rates curves, vol, commodity futures, DXY proxies, credit.
- **Event calendar**: consensus estimates + historical surprises.
- **News**: deduplicated, entity-tagged, relevance-scored streams.

Use ingestion jobs to store all records in a time-series/event store with UTC
timestamps, source quality tags, and entity links.

### 8) Safety, controls, and observability

- Hard constraints to avoid hallucinated catalysts (only cite retrieved events).
- Minimum evidence threshold before high-conviction calls.
- Drift monitor: track agent disagreement and confidence inflation.
- Full audit trail: prompt, retrieved docs, intermediate scores, final output.
- Human override mode for production alerts.

### 9) MVP implementation plan

**Phase 1 (1-2 weeks)**
- Build API + orchestrator + 3 agents (central-bank, news/event, seasonality).
- Implement normalized schema and basic weighted scoring.

**Phase 2 (2-4 weeks)**
- Add geopolitics and cross-asset regime agents.
- Add backtesting harness and confidence calibration.

**Phase 3**
- Add portfolio-level constraints, exposure netting, and signal decay optimization.

### 10) Example API response

```json
{
  "instrument": "EURUSD",
  "horizon": "1-2w",
  "bias": "bullish",
  "confidence": 67,
  "key_drivers": [
    "Relative policy repricing favors EUR leg",
    "Seasonal flow window supports EUR demand",
    "Risk sentiment stabilizing reduces USD safety bid"
  ],
  "known_risks": [
    "US inflation upside surprise",
    "Geopolitical escalation renewing USD safe-haven demand"
  ],
  "next_events": [
    "US CPI (2026-05-12)",
    "ECB speaker panel (2026-05-14)"
  ]
}
```
