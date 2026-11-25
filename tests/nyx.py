"""Live test harness for the nyx.cz API (stdlib only).

Token lookup order: env NYX_API_TOKEN, file from env NYX_ENV_FILE, ./.env.
Every call is recorded to tests/results/<segment>/<test_id>.json (gitignored).
Writes are restricted by ALLOWLIST; anything else raises before the request is sent.
"""
from __future__ import annotations

import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path

BASE = "https://nyx.cz/api"
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FIXTURES = ROOT / "fixtures"
PAUSE_S = 1.0

# --- safety allowlist -------------------------------------------------------
ALLOWLIST = {
    "discussion_ids": {288360},          # NYXOT ~ testing NYX API (owner NYXOT)
    "mail_recipients": {"BOD"},
    "rights_usernames": {"BOD"},
    "foreign_post_ids": {59141147},       # BOD's post in 288360
    "notification_token_prefix": "nyxapidoku-test-",
}
KNOWN_USERS = {"NYXOT", "BOD"}            # not anonymised in fixtures


class Forbidden(Exception):
    pass


def _load_token() -> str:
    tok = os.environ.get("NYX_API_TOKEN")
    if tok:
        return tok
    for p in filter(None, [os.environ.get("NYX_ENV_FILE"), str(Path.cwd() / ".env")]):
        if Path(p).is_file():
            for line in Path(p).read_text().splitlines():
                if line.startswith("NYX_API_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("NYX_API_TOKEN not found (set NYX_API_TOKEN or NYX_ENV_FILE)")


def nonce() -> str:
    """Unique marker for written content (nyx rejects duplicate texts)."""
    return f"[nyxapidoku {time.strftime('%Y-%m-%d %H:%M:%S')} {uuid.uuid4().hex[:6]}]"


@dataclass
class Result:
    status: int
    body: object          # parsed JSON or raw text
    headers: dict
    elapsed_ms: int

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


@dataclass
class Client:
    segment: str
    token: str = field(default_factory=_load_token)
    created: list = field(default_factory=list)   # cleanup registry: (kind, ids...)
    _last: float = 0.0

    # -- guard ---------------------------------------------------------------
    def _guard(self, method: str, path: str, params: dict, data: dict) -> None:
        q = {**(params or {}), **(data or {})}
        is_write = method != "GET" or re.search(r"/bookmark$", path) and "new_state" in q
        if not is_write:
            return
        A = ALLOWLIST
        m = re.match(r"/discussion/(\d+)/", path)
        if m and int(m.group(1)) not in A["discussion_ids"]:
            raise Forbidden(f"discussion {m.group(1)} not allowlisted")
        if path.startswith("/discussion/rights"):
            if int(q.get("discussion_id", 0)) not in A["discussion_ids"]:
                raise Forbidden("rights: discussion not allowlisted")
            if q.get("username") not in A["rights_usernames"]:
                raise Forbidden("rights: username not allowlisted")
        if path == "/mail/send" and q.get("recipient") not in A["mail_recipients"]:
            raise Forbidden("mail recipient not allowlisted")
        if path.startswith("/bookmarks/history/"):
            ids = q.get("discussion_ids") or []
            ids = ids if isinstance(ids, list) else [ids]
            if not ids or any(int(i) not in A["discussion_ids"] for i in ids):
                raise Forbidden("history: discussion_ids not allowlisted")
        if path.startswith("/file/delete/") or path.startswith("/file/embed/"):
            fid = int(path.split("/")[3])
            if ("file", fid) not in self.created:
                raise Forbidden(f"file {fid} not created by this run")
        if path.startswith("/register_for_notifications/"):
            if not path.split("/")[2].startswith(A["notification_token_prefix"]):
                raise Forbidden("notification token must be a fake test token")

    # -- request -------------------------------------------------------------
    def call(self, method: str, path: str, *, params: dict | None = None,
             data: dict | None = None, files: dict | None = None,
             auth: bool | str = True, test_id: str | None = None,
             claim: str = "") -> Result:
        """files = {"file": (filename, bytes, mime)}; data is form-encoded (lists → key[]).
        auth=False sends no header, auth="<str>" sends that token instead."""
        self._guard(method, path, params or {}, data or {})
        wait = PAUSE_S - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        url = BASE + path + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
        headers = {"Accept": "application/json", "User-Agent": "nyx_api_doku-tests/1.0"}
        if auth is True:
            headers["Authorization"] = f"Bearer {self.token}"
        elif isinstance(auth, str):
            headers["Authorization"] = f"Bearer {auth}"
        body = None
        if files:
            body, ctype = _multipart(data or {}, files)
            headers["Content-Type"] = ctype
        elif data is not None:
            pairs = []
            for k, v in data.items():
                if isinstance(v, list):
                    pairs += [(f"{k}[]", x) for x in v]
                else:
                    pairs.append((k, v))
            body = urllib.parse.urlencode(pairs).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        for attempt in range(4):
            t0 = time.time()
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    status, raw, hdrs = r.status, r.read(), dict(r.headers)
            except urllib.error.HTTPError as e:
                status, raw, hdrs = e.code, e.read(), dict(e.headers)
            except http.client.IncompleteRead:   # seen once on a ~480 kB search response
                self._last = time.time()
                time.sleep(2 ** (attempt + 1))
                status, raw, hdrs = -1, b"", {}
                continue
            self._last = time.time()
            if status != 429:
                break
            time.sleep(2 ** (attempt + 1))
        try:
            parsed = json.loads(raw) if raw else None
        except ValueError:
            parsed = raw.decode("utf-8", "replace")
        res = Result(status, parsed, hdrs, int((self._last - t0) * 1000))
        if test_id:
            self._record(test_id, claim, method, path, params, data, files, auth, res)
        return res

    def _record(self, test_id, claim, method, path, params, data, files, auth, res):
        d = RESULTS / self.segment
        d.mkdir(parents=True, exist_ok=True)
        rec = {
            "test_id": test_id, "claim": claim,
            "request": {"method": method, "path": path, "params": params, "data": data,
                        "files": {k: [v[0], len(v[1]), v[2]] for k, v in (files or {}).items()},
                        "auth": "token" if auth is True else ("none" if auth is False else "custom")},
            "status": res.status, "elapsed_ms": res.elapsed_ms,
            "content_type": res.headers.get("Content-Type"), "body": res.body,
        }
        (d / f"{test_id}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))


def _multipart(fields: dict, files: dict):
    b = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (fn, content, mime) in files.items():
        out += (f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{fn}"\r\n'
                f"Content-Type: {mime}\r\n\r\n").encode() + content + b"\r\n"
    out += f"--{b}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={b}"


# --- fixtures ---------------------------------------------------------------
def shrink(obj, max_items: int = 2, max_str: int = 200, _names=None):
    """Truncate lists/strings and anonymise unknown usernames for committed fixtures."""
    names = _names if _names is not None else {}
    if isinstance(obj, list):
        return [shrink(x, max_items, max_str, names) for x in obj[:max_items]]
    if isinstance(obj, dict):
        out = {}
        foreign = isinstance(obj.get("username"), str) and obj["username"] not in KNOWN_USERS
        for k, v in obj.items():
            if foreign and k in ("content", "content_raw", "title", "highlight") and v:
                out[k] = "<redacted>"
                continue
            if k in ("username", "nick", "user", "owner_username", "recipient", "sender") \
                    and isinstance(v, str) and v not in KNOWN_USERS:
                v = names.setdefault(v, f"USER{len(names) + 1}")
            out[k] = shrink(v, max_items, max_str, names)
        return out
    if isinstance(obj, str) and len(obj) > max_str:
        return obj[:max_str] + "…"
    return obj


def save_fixture(segment: str, name: str, body, **kw) -> Path:
    d = FIXTURES / segment
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{name}.json"
    p.write_text(json.dumps(shrink(body, **kw), ensure_ascii=False, indent=1) + "\n")
    return p


def shape(obj, depth: int = 0, max_depth: int = 4) -> object:
    """Type skeleton of a response, for comparing with Swagger schemas."""
    if depth > max_depth:
        return "…"
    if isinstance(obj, dict):
        return {k: shape(v, depth + 1, max_depth) for k, v in obj.items()}
    if isinstance(obj, list):
        return [shape(obj[0], depth + 1, max_depth)] if obj else []
    return type(obj).__name__ if obj is not None else "null"
