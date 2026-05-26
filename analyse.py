"""
analyse.py
Reads data/latest.json, sends it to Claude for trend analysis,
and writes a human-readable summary to data/analysis.json
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from collections import Counter

DATA_PATH     = os.path.join(os.path.dirname(__file__), "data", "latest.json")
ANALYSIS_PATH = os.path.join(os.path.dirname(__file__), "data", "analysis.json")
API_KEY       = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL         = "claude-sonnet-4-20250514"


def load_data() -> dict:
    with open(DATA_PATH) as f:
        return json.load(f)


def build_stats(items: list[dict]) -> dict:
    if not items:
        return {
            "total_reports": 0,
            "severity_counts": {},
            "top_programs": [],
            "top_weaknesses": [],
            "total_bounty_usd": 0,
            "avg_bounty_usd": 0,
            "paid_reports": 0,
        }
    severities   = Counter(i["severity"] for i in items)
    programs     = Counter(i["program"]  for i in items).most_common(5)
    weaknesses   = Counter(i["weakness"] for i in items).most_common(5)
    total_bounty = sum(i["bounty_usd"] for i in items)
    paid_reports = [i for i in items if i["bounty_usd"] > 0]
    return {
        "total_reports":    len(items),
        "severity_counts":  dict(severities),
        "top_programs":     programs,
        "top_weaknesses":   weaknesses,
        "total_bounty_usd": round(total_bounty, 2),
        "avg_bounty_usd":   round(total_bounty / len(paid_reports), 2) if paid_reports else 0,
        "paid_reports":     len(paid_reports),
    }


def call_claude(stats: dict, sample: list[dict]) -> str:
    if not API_KEY:
        print("  WARNING: ANTHROPIC_API_KEY secret not set — skipping AI analysis.")
        return "API key not configured. Add ANTHROPIC_API_KEY as a GitHub Secret."

    if stats["total_reports"] == 0:
        return "No reports collected in this run — skipping trend analysis."

    prompt = f"""You are a bug bounty intelligence analyst.
Analyse the following statistics from the latest HackerOne public disclosures
and provide a concise 3-5 bullet-point trend summary suitable for a security professional.

STATS:
{json.dumps(stats, indent=2)}

SAMPLE TITLES (first 10 reports):
{json.dumps([i['title'] for i in sample[:10]], indent=2)}

Focus on:
- Dominant vulnerability types and what that signals
- Severity distribution patterns
- Which programs are most active
- Any notable bounty trends
- One actionable insight for a bug bounty hunter

Respond in plain text with bullet points only. No preamble."""

    payload = json.dumps({
        "model":      MODEL,
        "max_tokens": 600,
        "messages":   [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         API_KEY,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  Claude API error {e.code}: {body}")
        # Don't crash the whole pipeline — return a fallback message
        return f"AI analysis unavailable (API error {e.code}). Check your ANTHROPIC_API_KEY secret."


def run():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting analysis…")
    data  = load_data()
    items = data.get("items", [])
    stats = build_stats(items)

    print(f"  Analysing {len(items)} reports…")
    summary = call_claude(stats, items)

    output = {
        "analysed_at": datetime.now(timezone.utc).isoformat(),
        "stats":       stats,
        "ai_summary":  summary,
    }
    with open(ANALYSIS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Analysis saved → {ANALYSIS_PATH}")
    print(f"\n--- AI SUMMARY ---\n{summary}\n------------------")
    return summary


if __name__ == "__main__":
    run()
