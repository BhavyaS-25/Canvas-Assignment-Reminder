import os
import sys
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import requests

# Required variables in .env file
# CANVAS_URL url of your canvas 
# CANVAS_API_KEY Canvas API access token
# NTFY_TOPIC ntfy topic for notifications
load_dotenv()

CANVAS_URL = os.environ["CANVAS_URL"].rstrip("/")
CANVAS_TOKEN = os.environ["CANVAS_TOKEN"]
NTFY_TOPIC = os.environ["NTFY_TOPIC"]
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
FREQUENCY = float(os.environ.get("LOOKAHEAD_HOURS", "24"))

INTERVALS = [
    (24, "24h"),
    (1, "1h"),
]
STATE_FILE = os.path.join(os.path.dirname(__file__), "notified_state.json")

HEADERS = {"Authorization": f"Bearer {CANVAS_TOKEN}"}

def canvas_get(path, params=None):
    url = f"{CANVAS_URL}/api/v1{path}"
    results = []
    while url:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        results.extend(response.json())
        url = None
        params = None  # only needed on first request
        link_header = response.headers.get("Link", "")
        for part in link_header.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return results

def get_active_courses():
    courses = canvas_get("/courses", params={"enrollment_state": "active", "per_page": 100})
    return [c for c in courses if not c.get("access_restricted_by_date")]

def get_upcoming_assignments(course_id, course_name):
    assignments = canvas_get(
        f"/courses/{course_id}/assignments",
        params={"bucket": "upcoming", "per_page": 100, "order_by": "due_at"},
    )
    out = []
    for a in assignments:
        if not a.get("due_at"):
            continue
        submission = a.get("submission") or {}
        if submission.get("workflow_state") == "submitted":
            continue
        out.append(
            {
                "id": a["id"],
                "name": a["name"],
                "due_at": a["due_at"],
                "course": course_name,
                "html_url": a.get("html_url", ""),
            }
        )
    return out

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()

def save_state(notified_ids):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(notified_ids), f)

def send_ntfy(assignment, hours_left, tier_label):
    due_local = datetime.fromisoformat(assignment["due_at"].replace("Z", "+00:00"))
    title = f"Due {tier_label}: {assignment['course']}"
    message = f"{assignment['name']}\nDue {due_local.strftime('%a %I:%M %p UTC')}"
 
    resp = requests.post(
        f"{NTFY_SERVER}/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "high" if hours_left <= 6 else "default",
            "Tags": "warning" if hours_left <= 6 else "book",
            "Click": assignment["html_url"] or CANVAS_URL,
        },
        timeout=15,
    )
    resp.raise_for_status() 

def main():
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=FREQUENCY)
    notified = load_state()
    newly_notified = set(notified)
    sent_count = 0

    courses = get_active_courses()
    for course in courses:
        course_name = course.get("name") or course.get("course_code") or "Course"
        try:
            assignments = get_upcoming_assignments(course["id"], course_name)
        except requests.HTTPError as e:
            print(f"Warning: failed to fetch assignments for {course_name}: {e}", file=sys.stderr)
            continue
 
        for a in assignments:
            due = datetime.fromisoformat(a["due_at"].replace("Z", "+00:00"))
            if due > window_end:
                continue
            if due < now:
                continue  

            hours_left = (due - now).total_seconds() / 3600

            for tier_hours, tier_label in INTERVALS:
                if hours_left > tier_hours:
                    continue
                state_key = f"{a['id']}:{tier_label}"
                if state_key in notified:
                    continue

                send_ntfy(a, hours_left, tier_label)
                newly_notified.add(state_key)
                sent_count += 1
                print(f"Notified ({tier_label}): {a['course']} - {a['name']} (due in {hours_left:.2f}h)")
                break  
    save_state(newly_notified)
    print(f"Done. {sent_count} notification(s) sent.")
 
if __name__ == "__main__":
     main() 
