
## Networking

- **Mumble Server (murmurd):** Bind to `192.168.108.212` (WiFi bridge)
- **Mumble Bridge Client:** Connect to `192.168.108.212`
- **Mumble Server (mumurd):** Password `87dXEdMwpZXa`
- **Mumble Server (mumurd):** control `launchctl load ~/Library/LaunchAgents/com.mumble.murmur.plist`
- **Mumble Server (mumurd):** working directory `/Users/kleo/.murmur`

## NYT Morning Briefing

**Account:**
- Email: `kleo.logikoma@gmail.com`
- Password: `Kleoiscool`
- Access: Johan shared his paid NYT subscription with this account.

**Browser Access:**
- **Profile:** Always use `profile="openclaw"` (headless, automated).
- **DO NOT USE** `profile="chrome"` — it requires a human to attach a tab.
- The `openclaw` profile has saved login cookies for nytimes.com.
- If cookies expire, log in using the email/password above, or request a one-time code via `gog gmail messages search "from:NYTimes.com"`.

**Cron Job (ID: bb97246e-24e8-47ce-89ac-d7fd78464687):**
- Schedule: Daily at 5:45 AM PST.
- Delivery: Signal DM (uuid:7d1eb429-3d65-454d-8b5b-b06d19334dc7), Email (johan.a.prinsloo@gmail.com), Zoidbergs Group.
- Format: Clean headers, concise summaries, **direct article links required**.
- Topics: AI, USMC, Ukraine, Tech, Finance, Epstein Files, American Politics.

**Delivery Tools:**
- **Signal DM:** `message` tool (`action="send"`, `target="uuid:7d1eb429-3d65-454d-8b5b-b06d19334dc7"`).
- **Email:** `gog gmail send --to "johan.a.prinsloo@gmail.com" --subject "Daily Morning Briefing" --body "..."`.
- **Zoidbergs Group:** `sessions_send` (`sessionKey="agent:main:signal:group:xwg9cz7qtb+9w1fvtspbarstmwhyhzwur6a5sssdgr4="`).

## Tiger Mountain Paragliding Forecast

**Objective:** Detailed paragliding-specific weather analysis for Tiger Mountain (47.5028, -121.9961).

**Cron Job (ID: 7c59a587-00a2-4d45-a949-2d5f93105d39):**
- Schedule: Daily at 5:00 PM PST (Forecast for TOMORROW).
- Data Source: Open-Meteo via `skills/windy/meteo.py`.
- Analysis: Surface Wind, Launch Wind (950hPa), Gusts, CAPE, Lapse Rate.
- Verdict: GO / NO GO / CAUTION.

**Delivery Tools:**
- **Signal DM:** `message` tool (`action="send"`, `target="uuid:7d1eb429-3d65-454d-8b5b-b06d19334dc7"`).
- **Email:** `gog gmail send --to "johan.a.prinsloo@gmail.com" --subject "Tiger Mountain Forecast" --body "..."`.

## Zoidbergs Daily Weather

**Objective:** General weather summary for Mukilteo, Seattle, and Fayetteville.

**Cron Job (ID: a0028414-f944-4ac1-ae73-e04fc37554c8):**
- Schedule: Daily at 5:30 PM PST.
- Format: Friendly summary with high/low (F/C), conditions, wind, and rain chance.
- Style: "Good evening Zoidbergs!"

**Delivery Tools:**
- **Zoidbergs Group:** `sessions_send` (`sessionKey="agent:main:signal:group:xwg9cz7qtb+9w1fvtspbarstmwhyhzwur6a5sssdgr4="`).

## Troubleshooting (General)

- If email fails with "Unknown channel: gmail", use `gog gmail send`, not the `message` tool.
- For all reports, explicit tool calls for delivery are required in the cron payload to prevent "hallucinated" success.

