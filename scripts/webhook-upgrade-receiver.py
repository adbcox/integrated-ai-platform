#!/usr/bin/env python3
"""Receives Diun webhook payloads and creates Plane issues for image updates."""
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from framework.plane_connector import PlaneAPI, RateLimitError  # noqa: E402

api = PlaneAPI()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        self.send_response(200)
        self.end_headers()

        entry = body.get("entry", {})
        image = entry.get("image", "unknown")
        new_tag = entry.get("new_tag", "?")
        old_tag = entry.get("old_tag", "?")

        title = f"[UPGRADE] {image}: {old_tag} → {new_tag}"
        desc = (
            f"Diun detected a new tag for `{image}`.\n\n"
            f"Old: `{old_tag}`\nNew: `{new_tag}`\n\n"
            f"Review changelog and update image pin in compose file."
        )
        try:
            issue = api.create_issue(name=title, description=desc, priority="low")
            print(f"Created Plane issue: {issue.get('id')} — {title}")
        except RateLimitError:
            time.sleep(60)
            try:
                api.create_issue(name=title, description=desc, priority="low")
            except Exception as e:
                print(f"Retry failed: {e}")
        except Exception as e:
            print(f"Failed to create issue: {e}")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8097))
    print(f"Upgrade receiver listening on :{port}")
    HTTPServer(("", port), Handler).serve_forever()
