#!/usr/bin/env python3
"""Sync Strava activities → Nextcloud CalDAV (training calendar).
Cron: 0 6 * * * ~/repos/integrated-ai-platform/scripts/sync-strava-to-calendar.py >> /var/log/strava-sync.log 2>&1
"""

import subprocess
import sys
import json
from datetime import datetime, timedelta, timezone

try:
    import requests
    from icalendar import Calendar, Event
    import pytz
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages",
                    "requests", "icalendar", "pytz"], check=True)
    import requests
    from icalendar import Calendar, Event
    import pytz

NEXTCLOUD_BASE = "http://192.168.10.145:8085/remote.php/dav/calendars/admin"
TRAINING_CAL  = f"{NEXTCLOUD_BASE}/training/"
VAULT_CONTAINER = "vault-server"
TOKEN_FILE = "/Users/admin/vault-init-keys.txt"


def vault_get(path: str, field: str) -> str:
    token = subprocess.run(["grep", "Initial Root Token", TOKEN_FILE],
                           capture_output=True, text=True).stdout.split()[-1]
    r = subprocess.run(
        ["docker", "exec", "-e", f"VAULT_TOKEN={token}", VAULT_CONTAINER,
         "vault", "kv", "get", f"-field={field}", path],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"Vault get {path}#{field} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def get_strava_activities(token: str, days: int = 30) -> list:
    after = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    r = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        params={"after": after, "per_page": 100},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def activity_to_ical(activity: dict) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//IAP Strava Sync//EN")
    cal.add("version", "2.0")

    ev = Event()
    start = datetime.fromisoformat(activity["start_date"].replace("Z", "+00:00"))
    elapsed = timedelta(seconds=activity["elapsed_time"])
    dist_km = activity.get("distance", 0) / 1000
    moving_min = activity.get("moving_time", 0) // 60
    elev = activity.get("total_elevation_gain", 0)

    ev.add("uid", f"strava-{activity['id']}@iap-nextcloud")
    ev.add("summary", f"🏃 {activity['type']}: {activity['name']}")
    ev.add("dtstart", start)
    ev.add("dtend", start + elapsed)
    ev.add("description",
           f"Distance: {dist_km:.2f} km\n"
           f"Moving time: {moving_min} min\n"
           f"Elevation gain: {elev:.0f} m\n"
           f"Strava ID: {activity['id']}")
    ev.add("categories", [activity["type"]])
    cal.add_component(ev)
    return cal.to_ical()


def push_event(activity: dict, nc_user: str, nc_pass: str) -> bool:
    uid = f"strava-{activity['id']}.ics"
    r = requests.put(
        f"{TRAINING_CAL}{uid}",
        data=activity_to_ical(activity),
        headers={"Content-Type": "text/calendar; charset=utf-8"},
        auth=(nc_user, nc_pass),
        timeout=15,
    )
    return r.status_code in (200, 201, 204)


def main():
    print(f"{datetime.now().isoformat()} — Strava → Nextcloud Calendar sync starting")
    try:
        access_token = vault_get("secret/strava/oauth", "access_token")
        nc_user = vault_get("secret/nextcloud/admin", "username")
        nc_pass = vault_get("secret/nextcloud/admin", "password")
    except RuntimeError as e:
        print(f"❌ Vault error: {e}")
        print("  Ensure Strava credentials stored: vault kv put secret/strava/oauth client_id=... client_secret=... refresh_token=...")
        sys.exit(1)

    activities = get_strava_activities(access_token)
    print(f"Found {len(activities)} activities in last 30 days")

    synced = errors = 0
    for act in activities:
        try:
            ok = push_event(act, nc_user, nc_pass)
            if ok:
                synced += 1
                print(f"  ✅ {act['type']}: {act['name']} ({act['start_date'][:10]})")
            else:
                errors += 1
                print(f"  ⚠️  {act['name']} — unexpected status")
        except Exception as exc:
            errors += 1
            print(f"  ❌ {act['name']} — {exc}")

    print(f"Done: {synced} synced, {errors} errors")


if __name__ == "__main__":
    main()
