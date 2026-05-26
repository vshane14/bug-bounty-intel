"""
notify.py
Sends an email summary after the daily collection + analysis run.
Uses Python's smtplib with Gmail SMTP (or any SMTP provider).

Required environment variables (set as GitHub Secrets):
  NOTIFY_EMAIL      — address to send TO (and FROM, if using Gmail)
  NOTIFY_PASSWORD   — Gmail App Password (NOT your main Gmail password)
                      Create one at: https://myaccount.google.com/apppasswords

Optional:
  SMTP_HOST         — defaults to smtp.gmail.com
  SMTP_PORT         — defaults to 587
"""

import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ANALYSIS_PATH = os.path.join(os.path.dirname(__file__), "data", "analysis.json")
DATA_PATH     = os.path.join(os.path.dirname(__file__), "data", "latest.json")

TO_EMAIL      = os.environ.get("NOTIFY_EMAIL", "")
FROM_EMAIL    = os.environ.get("NOTIFY_FROM_EMAIL", TO_EMAIL)
PASSWORD      = os.environ.get("NOTIFY_PASSWORD", "")
SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))


def load_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def build_email_body(analysis: dict, data: dict) -> tuple[str, str]:
    """Returns (plain_text, html) email body."""
    stats   = analysis.get("stats", {})
    summary = analysis.get("ai_summary", "Analysis not available.")
    fetched = data.get("fetched_at", "unknown")
    total   = stats.get("total_reports", 0)
    severities = stats.get("severity_counts", {})
    top_programs = stats.get("top_programs", [])
    avg_bounty = stats.get("avg_bounty_usd", 0)

    sev_lines = "\n".join(
        f"  • {k.upper()}: {v}" for k, v in severities.items()
    )
    prog_lines = "\n".join(
        f"  • {name}: {count} reports" for name, count in top_programs
    )

    plain = f"""Bug Bounty Intel — Daily Update
================================
Fetched: {fetched}
Total reports: {total}

SEVERITY BREAKDOWN
{sev_lines}

TOP ACTIVE PROGRAMS
{prog_lines}

Average bounty: ${avg_bounty:,.2f}

AI TREND SUMMARY
{summary}

---
View full dashboard: https://vshane14.github.io/bug-bounty-intel
"""

    html = f"""
<html><body style="font-family:monospace;background:#04080f;color:#c8daf0;padding:24px;">
  <h2 style="color:#00d4ff;">🔍 Bug Bounty Intel — Daily Update</h2>
  <p style="color:#5a7a9e;">Fetched: {fetched}</p>
  <p><strong>{total}</strong> reports collected</p>

  <h3 style="color:#00d4ff;">Severity Breakdown</h3>
  <ul>
    {"".join(f'<li><strong>{k.upper()}</strong>: {v}</li>' for k, v in severities.items())}
  </ul>

  <h3 style="color:#00d4ff;">Top Active Programs</h3>
  <ul>
    {"".join(f'<li>{name}: {count} reports</li>' for name, count in top_programs)}
  </ul>

  <p>Average bounty: <strong>${avg_bounty:,.2f}</strong></p>

  <h3 style="color:#00d4ff;">AI Trend Summary</h3>
  <pre style="background:#0d1525;padding:16px;border-radius:8px;color:#39ff8f;">{summary}</pre>

  <hr style="border-color:#1a2640;">
  <p style="color:#5a7a9e;">
    <a href="https://vshane14.github.io/bug-bounty-intel" style="color:#00d4ff;">
      View full dashboard →
    </a>
  </p>
</body></html>
"""
    return plain, html


def run():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Sending notification…")

    if not TO_EMAIL or not PASSWORD:
        print("  NOTIFY_EMAIL or NOTIFY_PASSWORD not set — skipping email.")
        return

    analysis = load_json(ANALYSIS_PATH)
    data     = load_json(DATA_PATH)
    plain, html = build_email_body(analysis, data)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔍 Bug Bounty Intel Daily Update — {today}"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = TO_EMAIL
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(FROM_EMAIL, PASSWORD)
        server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())

    print(f"  Email sent to {TO_EMAIL}")


if __name__ == "__main__":
    run()
