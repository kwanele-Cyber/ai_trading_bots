"""Fundamental FX analysis bot.

Runs twice daily and builds a forward-looking narrative for selected FX pairs
using central-bank policy context, seasonality, macro calendar risk, geopolitics,
trade/tariff headlines, and major-bank research narratives.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import logging
import os
from typing import Iterable

import requests
from apscheduler.schedulers.blocking import BlockingScheduler


@dataclasses.dataclass
class Persona:
    name: str
    role: str
    objective: str


@dataclasses.dataclass
class BotConfig:
    pairs: list[str]
    run_hours_utc: tuple[int, int] = (6, 18)
    openai_api_key: str = dataclasses.field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = "gpt-5.3-codex"


class FundamentalFXBot:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.personas = [
            Persona(
                name="CentralBankWatcher",
                role="Macro policy analyst",
                objective="Map central-bank mandates and reaction functions to probable policy paths.",
            ),
            Persona(
                name="GeopoliticalRiskLead",
                role="Geopolitical and trade risk specialist",
                objective="Identify geopolitical and tariff catalysts likely to shift growth, inflation, or risk sentiment.",
            ),
            Persona(
                name="FlowAndSeasonalityDesk",
                role="FX flow strategist",
                objective="Evaluate seasonality windows, positioning, and timing asymmetry for the pair.",
            ),
            Persona(
                name="SellSideNarrativeAggregator",
                role="Institutional research synthesizer",
                objective="Extract consensus/divergence in major-bank narratives and key invalidation levels.",
            ),
        ]

    def run(self) -> None:
        """Main job: collect context, build a forward-looking report per pair."""
        now = dt.datetime.now(dt.UTC)
        logging.info("Starting fundamental run at %s", now.isoformat())

        for pair in self.config.pairs:
            context = self._collect_context(pair)
            report = self._build_forward_guidance(pair, context)
            self._store_report(pair, report, now)
            logging.info("Finished report for %s", pair)

    def _collect_context(self, pair: str) -> dict:
        return {
            "pair": pair,
            "timestamp": dt.datetime.now(dt.UTC).isoformat(),
            "central_bank": self._central_bank_context(pair),
            "seasonality": self._seasonality_context(pair),
            "event_risk": self._event_risk_context(pair),
            "geopolitics_and_tariffs": self._geopolitical_context(pair),
            "bank_narratives": self._major_bank_narratives(pair),
        }

    def _central_bank_context(self, pair: str) -> dict:
        base, quote = pair[:3], pair[3:]
        return {
            "mandate_map": {
                base: "inflation + employment/financial stability (country specific)",
                quote: "inflation + employment/financial stability (country specific)",
            },
            "next_decisions": "stub",
            "policy_bias": "stub (hawkish/neutral/dovish)",
        }

    def _seasonality_context(self, pair: str) -> dict:
        return {"monthly_pattern": "stub", "flow_windows": "stub"}

    def _event_risk_context(self, pair: str) -> dict:
        return {"next_two_weeks": ["stub event 1", "stub event 2"]}

    def _geopolitical_context(self, pair: str) -> dict:
        return {"headline_risks": ["stub geopolitical risk"], "tariff_risks": ["stub tariff risk"]}

    def _major_bank_narratives(self, pair: str) -> dict:
        return {"consensus": "stub", "dispersion": "stub"}

    def _call_llm(self, system_prompt: str, input_prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.config.openai_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.config.openai_model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_prompt},
            ],
        }
        resp = requests.post("https://api.openai.com/v1/responses", headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("output_text", "")

    def _run_persona_chain(self, pair: str, context: dict) -> dict:
        outputs: dict[str, str] = {}
        base_context = json.dumps(context)

        for persona in self.personas:
            system_prompt = (
                f"You are {persona.name}, acting as a {persona.role}. "
                f"Objective: {persona.objective} "
                "Focus only on forward-looking catalysts and scenario probabilities."
            )
            prompt = (
                f"Pair: {pair}\n"
                f"Context: {base_context}\n"
                "Return concise bullets with: likely catalyst, direction bias, timing window, invalidation."
            )
            outputs[persona.name] = self._call_llm(system_prompt, prompt)

        return outputs

    def _build_forward_guidance(self, pair: str, context: dict) -> str:
        if not self.config.openai_api_key:
            return "OPENAI_API_KEY missing; dry-run only."

        persona_views = self._run_persona_chain(pair, context)
        system_prompt = (
            "You are a chief FX strategist. Synthesize multiple analyst personas into an execution-ready "
            "forward guidance memo. Prioritize what can move price next, not backward descriptions."
        )
        prompt = (
            f"Pair: {pair}\n"
            f"Context: {json.dumps(context)}\n"
            f"Persona outputs: {json.dumps(persona_views)}\n"
            "Produce: baseline scenario, bullish scenario, bearish scenario, trigger checklist, and risk controls."
        )
        return self._call_llm(system_prompt, prompt)

    def _store_report(self, pair: str, report: str, now: dt.datetime) -> None:
        out_dir = "reports"
        os.makedirs(out_dir, exist_ok=True)
        fname = f"{out_dir}/{pair}_{now.strftime('%Y%m%dT%H%M%SZ')}.md"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"# {pair} Forward Guidance\n\n")
            f.write(report)


def validate_pairs(pairs: Iterable[str]) -> list[str]:
    cleaned = []
    for p in pairs:
        p2 = p.strip().upper().replace("/", "")
        if len(p2) != 6 or not p2.isalpha():
            raise ValueError(f"Invalid pair: {p}")
        cleaned.append(p2)
    return cleaned


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    pairs = validate_pairs(os.getenv("FX_PAIRS", "EURUSD,GBPUSD,USDJPY,AUDNZD").split(","))
    config = BotConfig(pairs=pairs)

    bot = FundamentalFXBot(config)
    scheduler = BlockingScheduler(timezone="UTC")
    for hour in config.run_hours_utc:
        scheduler.add_job(bot.run, "cron", hour=hour, minute=0)

    logging.info("Scheduler started for UTC hours=%s pairs=%s", config.run_hours_utc, pairs)
    bot.run()
    scheduler.start()


if __name__ == "__main__":
    main()
