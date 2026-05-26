# Bug Bounty Intel

Automated daily intelligence on HackerOne public disclosures, powered by Claude AI.

## What it does

Every day at 08:00 UTC this agent:
1. **Fetches** the latest ~100 public bug bounty disclosures from HackerOne
2. **Analyses** trends using Claude AI
3. **Emails** you a summary
4. **Commits** fresh data so the dashboard always shows live results

## Setup (one time)

### 1. Fork / clone this repo
Create a new repo on GitHub and upload all these files.

### 2. Add GitHub Secrets
Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these three secrets:

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Claude API key from [console.anthropic.com](https://console.anthropic.com) |
| `NOTIFY_EMAIL` | The email address you want updates sent to |
| `NOTIFY_FROM_EMAIL` | The Gmail address you're sending *from* |
| `NOTIFY_PASSWORD` | A Gmail **App Password** (see below) |

### 3. Create a Gmail App Password
Regular Gmail passwords won't work. You need an App Password:
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select **Mail** + **Other (custom name)** → name it "Bug Bounty Intel"
3. Copy the 16-character password → use it as `NOTIFY_PASSWORD`

### 4. Run manually to test
Go to **Actions** tab → **Daily Bug Bounty Intel** → **Run workflow** → **Run workflow**

Watch the logs — you should see data collected, analysed, and an email arrive.

## Files

```
├── collector.py              # Fetches HackerOne data
├── analyse.py                # Claude AI trend analysis  
├── notify.py                 # Sends email summary
├── data/
│   ├── latest.json           # Raw report data (auto-updated daily)
│   └── analysis.json         # AI summary + stats (auto-updated daily)
└── .github/
    └── workflows/
        └── daily.yml         # The schedule that runs everything
```

## Schedule

Runs daily at **08:00 UTC** (09:00 London BST / 08:00 GMT).

To change the time, edit the `cron` line in `.github/workflows/daily.yml`.
`"0 8 * * *"` = minute 0, hour 8, every day.
