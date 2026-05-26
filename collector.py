"""
collector.py
Fetches the latest public bug bounty disclosures from HackerOne's
public GraphQL API and saves them to data/latest.json
"""

import json
import os
import time
from datetime import datetime, timezone
import urllib.request
import urllib.error

GRAPHQL_URL = "https://hackerone.com/graphql"

QUERY = """
query {
  hacktivity_items(
    first: 100
    order_by: { field: latest_disclosable_activity_at, direction: DESC }
    where: { report: { disclosed_at: { _is_null: false } } }
  ) {
    edges {
      node {
        ... on HacktivityItem {
          databaseId: _id
          report {
            title
            substate
            severity_rating
            disclosed_at
            total_awarded_amount
            url
            weakness {
              name
            }
          }
          team {
            name
            url
          }
        }
      }
    }
  }
}
"""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BugBountyIntel/1.0)",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "latest.json")


def fetch_hacktivity() -> list[dict]:
    payload = json.dumps({"query": QUERY}).encode()
    req = urllib.request.Request(GRAPHQL_URL, data=payload, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode())
            edges = (
                raw.get("data", {})
                   .get("hacktivity_items", {})
                   .get("edges", [])
            )
            return [e["node"] for e in edges if e.get("node")]
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} from HackerOne GraphQL — {e.reason}")
        return []
    except Exception as e:
        print(f"  Error fetching data: {e}")
        return []


def normalise(node: dict) -> dict:
    report = node.get("report") or {}
    team   = node.get("team")   or {}
    weakness = report.get("weakness") or {}
    bounty = report.get("total_awarded_amount") or 0
    return {
        "id":           node.get("databaseId", ""),
        "title":        report.get("title", "Untitled"),
        "severity":     (report.get("severity_rating") or "none").lower(),
        "bounty_usd":   float(bounty) if bounty else 0.0,
        "disclosed_at": report.get("disclosed_at", ""),
        "program":      team.get("name", "Unknown"),
        "url":          report.get("url", ""),
        "weakness":     weakness.get("name", "Unknown"),
    }


def run():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting collector…")
    nodes = fetch_hacktivity()
    print(f"  Fetched {len(nodes)} raw items from HackerOne")

    items = [normalise(n) for n in nodes]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total":      len(items),
        "items":      items,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Saved {len(items)} reports → {OUTPUT_PATH}")
    return len(items)


if __name__ == "__main__":
    run()
