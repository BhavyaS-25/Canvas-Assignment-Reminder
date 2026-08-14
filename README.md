# Canvas Assignment Reminders

Automatically checks Canvas for upcoming assignments and sends push
notifications to my iPhone as deadlines approach — first a 24-hour warning,
then a 1-hour warning. Runs on a schedule in GitHub Actions, so it works
even when my laptop is off.

## How it works

1. A Python script (`reminder.py`) authenticates with the Canvas REST API,
   pulls all active courses, and checks each course's upcoming assignments.
2. For each assignment, it checks how far away the due date is against a set
   of reminder "tiers" (24h, 1h). If a tier applies and hasn't already been
   sent, it fires a push notification via [ntfy](https://ntfy.sh).
3. Sent notifications are tracked in `notified_state.json` so the same
   reminder never fires twice.
4. A GitHub Actions workflow runs the script every 30 minutes, injects
   credentials via encrypted repo secrets, and commits the updated state
   file back to the repo after each run.

## Setup

### 1. Get a Canvas API token
Canvas → Account → Settings → Approved Integrations → **+ New Access Token**.
Copy it immediately — it's only shown once.

### 2. Set up ntfy on your phone
Install the free **ntfy** app (iOS/Android), tap **+**, and subscribe to a
private, hard-to-guess topic name (e.g. `yourname-canvas-a91f3`). No account
needed — topics are just a shared secret string.

### 3. Clone this repo and install dependencies
```bash
git clone <your-repo-url>
cd assignment-reminder
python3 -m venv .venv
source .venv/bin/activate      # .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 4. Create a local `.env` file
```
CANVAS_URL=https://gatech.instructure.com
CANVAS_TOKEN=your-token-here
NTFY_TOPIC=your-topic-name
```
`.env` is git-ignored and never committed.

### 5. Test locally
```bash
python reminder.py
```
Check the printed output for `Done. X notification(s) sent.`

### 6. Deploy to GitHub Actions
Add three repository secrets (**Settings → Secrets and variables →
Actions**): `CANVAS_URL`, `CANVAS_TOKEN`, `NTFY_TOPIC`. The workflow in
`.github/workflows/canvas-reminders.yml` picks these up automatically and
runs on its own schedule — no server required.

## Configuration

Reminder tiers live in `reminder.py`:
```python
INTERVALS = [
    (24, "24h"),
    (1, "1h"),
]
```
Add or adjust tuples (hours-before-due, label) to change when reminders
fire. The schedule frequency (currently every 30 minutes) is set via the
`cron` line in the workflow file — it should be tighter than your shortest
tier to reliably catch it in time.

## Tech stack
- Python (`requests` for the Canvas REST API, handling pagination via the
  `Link` header)
- GitHub Actions (scheduled/cron-based serverless execution)
- ntfy (push notification delivery)
- JSON file for idempotent state tracking across runs
