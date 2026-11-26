"""Snapshot of state that write tests may change (read-only GETs).

Saves to tests/results/_backup/<timestamp>/ (gitignored). Run before Phase 2.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nyx import RESULTS, Client  # noqa: E402

TARGETS = {
    "discussion_288360": ("/discussion/288360", None),
    "bookmarks": ("/bookmarks", None),
    "bookmarks_all": ("/bookmarks/all", None),
    "bookmarks_history": ("/bookmarks/history", {"show_read": "true", "show_booked": "true"}),
    "notifications": ("/notifications", None),
}

if __name__ == "__main__":
    c = Client("_backup")
    out = RESULTS / "_backup" / time.strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True)
    for name, (path, params) in TARGETS.items():
        r = c.call("GET", path, params=params)
        (out / f"{name}.json").write_text(json.dumps(
            {"status": r.status, "body": r.body}, ensure_ascii=False, indent=1))
        print(f"{name}: {r.status}")
    print(out)
