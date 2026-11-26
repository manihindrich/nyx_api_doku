"""Compare fields of real responses (tests/results) with Swagger schemas.

Usage: python3 -I tests/models_check.py <swagger.json>
Prints, per model: fields seen in responses (with how often), fields only in Swagger,
fields only in responses. Reads tests/results/*/T-*.json (local, gitignored).
"""
import collections
import glob
import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"


def props(spec, name, seen=None):
    """Property names of a schema, resolving $ref and allOf."""
    seen = seen or set()
    if name in seen:
        return set()
    seen.add(name)
    s = spec["components"]["schemas"][name]
    out = set(s.get("properties", {}))
    for part in s.get("allOf", []):
        if "$ref" in part:
            out |= props(spec, part["$ref"].split("/")[-1], seen)
        out |= set(part.get("properties", {}))
    return out


def walk(obj, path=""):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for x in obj:
            yield from walk(x, path + "[]")


# model name -> (segment glob, JSON path suffix of objects of that model)
SOURCES = {
    "Context": [("*", ".context")],
    "User": [("*", ".context.user")],
    "Activity": [("*", ".activity")],
    "DiscussionPostWithName (discussion posts)": [("discussion", ".posts[]")],
    "TemplatePost (last, search)": [("last", ".posts[]"), ("search", ".posts[]")],
    "MailPost": [("mail", ".posts[]")],
    "MailConversationWithActivity": [("mail", ".conversations[]")],
    "BookmarkedDiscussion": [("bookmarks", ".discussions[]"), ("bookmarks", ".bookmarks[].bookmarks[]")],
    "FileWithUrl": [("file", "")],
    "Notification": [("notifications", ".notifications[]")],
    "NotificationThumbUp": [("notifications", ".details.thumbs_up[]")],
}
SCHEMA = {
    "DiscussionPostWithName (discussion posts)": "DiscussionPostWithName",
    "TemplatePost (last, search)": "TemplatePost",
}


def main(spec_path):
    spec = json.load(open(spec_path))
    for model, sources in SOURCES.items():
        counts, n = collections.Counter(), 0
        for seg, suffix in sources:
            for f in glob.glob(str(RESULTS / seg / "T-*.json")):
                rec = json.load(open(f))
                if not (200 <= rec["status"] < 300) or rec["request"]["method"] != ("PUT" if seg == "file" else "GET"):
                    continue
                for p, o in walk(rec["body"]):
                    if p.endswith(suffix) and (suffix or p == ""):
                        n += 1
                        counts.update(o.keys())
        if not n:
            continue
        sw = props(spec, SCHEMA.get(model, model.split(" ")[0]))
        print(f"## {model}  ({n} objects)")
        print("  seen:", ", ".join(f"{k}{'' if c == n else f' ({c}/{n})'}" for k, c in sorted(counts.items())))
        print("  only in Swagger:", ", ".join(sorted(sw - set(counts))) or "-")
        print("  only in responses:", ", ".join(sorted(set(counts) - sw)) or "-")


if __name__ == "__main__":
    main(sys.argv[1])
