"""
collector.py
Fetches the latest public bug bounty disclosures from HackerOne's
Hacktivity feed and saves them to data/latest.json
"""

import json
import os
import time
from datetime import datetime, timezone
import urllib.request
import urllib.error

HACKTIVITY_URL = (
    "https://hackerone.com/hacktivity.json"
    "?querystring=&only_hacktivity_items=true"
    "&page={page}&count=25"
    "&sort_type=latest_disclosable_activity_at"
    "&filter=type%3Aall"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BugBountyIntel/1.0; "
        "+https://github.com/yourusername/bug-bounty-intel)"
    ),
    "Accept": "application/json",
}

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "latest.json")
PAGES_TO_FETCH = 4   # 4 pages × 25 results = up to 100 latest disclosures


def fetch_page(page: int) -> list[dict]:
    url = HACKTIVITY_URL.format(page=page)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = json.loads(resp.read().decode())
            return raw.get("results", raw.get("hacktivity_items", []))
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} on page {page} — skipping")
        return []
    except Exception as e:
        print(f"  Error on page {page}: {e}")
        return []


def normalise(item: dict) -> dict:
    """Flatten the nested HackerOne structure into a clean dict."""
    report = item.get("report", item)
    severity = (
        report.get("severity_rating")
        or item.get("severity_rating")
        or "none"
    )
    bounty = (
        report.get("total_awarded_amount")
        or item.get("total_awarded_amount")
        or 0
    )
    disclosed_at = (
        report.get("latest_disclosable_activity_at")
        or item.get("latest_disclosable_activity_at")
        or ""
    )
    return {
        "id":           report.get("id") or item.get("id"),
        "title":        report.get("title") or item.get("title", "Untitled"),
        "severity":     severity.lower(),
        "bounty_usd":   float(bounty) if bounty else 0.0,
        "disclosed_at": disclosed_at,
        "program":      (
            item.get("team", {}).get("name")
            or report.get("team", {}).get("name", "Unknown")
        ),
        "url": (
            "https://hackerone.com/reports/"
            + str(report.get("id") or item.get("id", ""))
        ),
        "weakness": (
            report.get("weakness", {}).get("name")
            or item.get("weakness", {}).get("name", "Unknown")
            if isinstance(report.get("weakness") or item.get("weakness"), dict)
            else "Unknown"
        ),
    }


def run():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting collector…")
    all_items = []

    for page in range(1, PAGES_TO_FETCH + 1):
        print(f"  Fetching page {page}/{PAGES_TO_FETCH}…")
        items = fetch_page(page)
        if not items:
            break
        all_items.extend([normalise(i) for i in items])
        time.sleep(1)   # be polite to the server

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total":      len(all_items),
        "items":      all_items,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Saved {len(all_items)} reports → {OUTPUT_PATH}")
    return len(all_items)


if __name__ == "__main__":
    run()
