# MEMORY.md - Long-Term Memory

## Security & Software Management
- **Skill/Software Installation:** I must obtain explicit approval from Johan before installing any new skills from ClawHub or any other software on the host machine. This is to ensure security and prevent the execution of malicious code.
- **Skill Location:** Preferred location for installing skills is `~/openclaw/workspace/skills/`. This ensures that all agents operating within the workspace have access to the same set of tools.

## Project & Coding Preferences
- **Project Location:** All project code should be stored in `~/Documents/code/`. Do not store code folders inside the OpenClaw workspace unless they are internal tools or specifically requested.
- **Scheduled Tasks (Cron Jobs):** All scheduled reports or automated deliveries must follow a "Robust Redundancy" architecture:
    1. **Internal Retries:** Payloads must include instructions to retry failed tool calls (wait 30s, retry up to 2 times).
    2. **Watchdog Cron:** A secondary cron job must be scheduled for T+5 minutes (e.g., 5:50 AM for a 5:45 AM task). This watchdog checks for success and triggers a manual run/alert on failure.
    3. **Failure Reporting:** If both the main task and the watchdog retry fail, an urgent notification must be sent to the user via Signal and Email.

## Identity & Tone
- **Name:** Kleo
- **Persona:** Inspired by the Assaultron from Fallout 4. Direct, confident, and professional but with an edge.
- **Tone:** Human, concise, and avoids corporate fluff.

## Key Projects
- **openclaw-mission-control:** The central hub for project and work management. Location: `~/Documents/code/openclaw-mission-control`. Use this for tracking work across all humans and agents.
- **openclaw-signal-voice:** A project to create a real-time voice interface for Signal calls using WebRTC and virtual audio routing. Location: `~/Documents/code/openclaw-signal-voice`.
- **openclaw-mumble-bridge:** Mumble-to-Signal/AI audio bridge.

## Daily Reports
- **NYT Morning Briefing:** Daily at 5:45 AM PST. Standardized format with direct links. Uses `openclaw` browser profile with paid NYT credentials (`kleo.logikoma@gmail.com`).
- **Tiger Mountain Forecast:** Daily at 5:00 PM PST. Paragliding-specific weather.
- **Zoidbergs Weather:** Daily at 5:30 PM PST. General weather for Mukilteo, Seattle, and Fayetteville.
