"""Live test for segment `html`: what nyx keeps, changes or removes in HTML of posts and mail.

Writes: 2 posts in the test discussion (deleted in finally), 1 mail to the peer user (cannot be deleted).
Guard-enforced by nyx.py. Each case is one numbered line of one document ([NN] marker).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from http.client import IncompleteRead  # noqa: E402
from nyx import Client, Result, nonce, save_fixture  # noqa: E402
from nyx import TEST_USER, PEER_USER, TEST_DISC, PUBLIC_DISC  # noqa: E402

SEG = "html"
DISC = TEST_DISC            # "test discussion": the only discussion written to
DP = f"/discussion/{DISC}"
c = Client(SEG)
_n = [0]
N_CASES = 34

DOC_CASES_SRC = r'''
01 <b>b</b>
02 <i>i</i>
03 <u>u</u>
04 <s>s</s>
05 <a href="https://example.com">link</a>
06 <a href="https://example.com" target="_blank">t</a>
07 <img src="https://nyx.cz/favicon.ico" width="16">
08 <font color="red">red</font>
09 <font size="1">small font</font>
10 <center>c</center>
11 <pre>pre  text</pre>
12 <small>small</small>
13 <h2>h2</h2>
14 a<br>b
15 <hr>
16 <code>x = 1</code>
17 <div class='spoiler'>spoiler</div>
18 (fence below)
```txt
fenced block
```
19 <xmp><b>x</b></xmp>
20 <script>alert(1)</script>
21 <style>body{color:red}</style>
22 <iframe src="https://example.com"></iframe>
23 <b onclick="alert(1)">onclick</b>
24 <a href="javascript:alert(1)">js</a>
25 <a href="https://example.com" title="https://example.com">title with url</a>
26 <a href="https://example.com" title="plain title">title plain</a>
27 bare URL https://example.com/path
28 discussion URL https://nyx.cz/discussion/PUBLIC_DISC_ID
29 <span style="color:red">span style</span>
30 <table><tr><td>td</td></tr></table>
31 <ul><li>li</li></ul>
32 <blockquote>q</blockquote>
33 &lt;escaped&gt; &amp;
34 line A
line B
'''


def C(*a, **k):
    """Transport errors become status -1 (no retry here; nyx.py itself may retry a truncated read)."""
    try:
        return c.call(*a, **k)
    except (IncompleteRead, OSError) as e:
        return Result(-1, f"transport: {type(e).__name__}: {e}"[:200], {}, 0)


def tid():
    _n[0] += 1
    return f"T-{SEG}-{_n[0]:02d}"


def parse_cases():
    cases = []
    for line in DOC_CASES_SRC.replace("PUBLIC_DISC_ID", str(PUBLIC_DISC)).strip("\n").split("\n"):
        m = re.match(r"^(\d\d) (.*)$", line)
        if m:
            cases.append([int(m.group(1)), m.group(2)])
        else:
            cases[-1][1] += "\n" + line          # continuation line of a multi-line case
    assert [num for num, _ in cases] == list(range(1, N_CASES + 1)), "case numbering broken"
    return [(num, text) for num, text in cases]


def build(cases, n):
    lines = [f"[{num:02d}] {text}" for num, text in cases]
    lines[0] += " " + n                          # nonce() in the first line
    return "\n".join(lines)


def posts_in(r):
    if r.status == 200 and isinstance(r.body, dict) and isinstance(r.body.get("posts"), list):
        return [p for p in r.body["posts"] if isinstance(p, dict)]
    return []


def find_by(posts, n):
    hits = [p for p in posts if n in (p.get("content") or "")]
    return hits[0] if hits else None


def disc_send(fmt, cases):
    n = nonce()
    doc = build(cases, n)
    t = tid()
    r = C("POST", f"{DP}/send/text", data={"content": doc, "format": fmt}, test_id=t,
          claim=f"undocumented: stored form of a post sent with format={fmt} (Swagger send/text: text|html)")
    print(f"{t} | {r.status} | send discussion format={fmt} | body={r.body!r}"[:300])
    g = C("GET", DP, params={"user": TEST_USER, "order": "newest"}, test_id=tid(),
          claim="undocumented: stored content of the sent post (GET /discussion/{id})")
    p = find_by(posts_in(g), n)
    if p is None:
        print(f"  format={fmt}: post with nonce NOT found after send (status {r.status})")
        return {"format": fmt, "id": None, "nonce": n, "input": doc, "content": None, "content_raw": None}
    c.created.append(("post", p["id"]))          # registered right after the id is known
    print(f"  format={fmt}: post id={p['id']} registered for deletion")
    return {"format": fmt, "id": p["id"], "nonce": n, "input": doc,
            "content": p.get("content"), "content_raw": p.get("content_raw")}


def mail_send(cases):
    n = nonce()
    doc = build(cases, n)
    t = tid()
    r = C("POST", "/mail/send", data={"recipient": PEER_USER, "message": doc, "format": "html"}, test_id=t,
          claim="undocumented: stored form of mail sent with format=html (Swagger mail/send: text|html)")
    print(f"{t} | {r.status} | send mail to {PEER_USER} format=html | body={r.body!r}"[:300])
    g = C("GET", "/mail", params={"user": PEER_USER, "order": "newest"}, test_id=tid(),
          claim="undocumented: stored content of the sent mail (GET /mail)")
    p = find_by(posts_in(g), n)
    if p is None:
        print(f"  mail: post with nonce NOT found after send (status {r.status})")
        return {"format": "html", "id": None, "nonce": n, "input": doc, "content": None, "content_raw": None}
    c.created.append(("mail", p["id"]))          # mail cannot be deleted; registered for the record only
    print(f"  mail: id={p['id']}")
    return {"format": "html", "id": p["id"], "nonce": n, "input": doc,
            "content": p.get("content"), "content_raw": p.get("content_raw")}


def delete_and_verify(res):
    pids = [i for k, i in c.created if k == "post"]
    for pid in pids:
        t = tid()
        r = C("DELETE", f"{DP}/delete/{pid}", test_id=t,
              claim="DELETE /discussion/{discussion_id}/delete/{id} (own post registered by this run)")
        print(f"{t} | {r.status} | delete post {pid} | body={r.body!r}"[:300])
    g = C("GET", DP, params={"user": TEST_USER, "order": "newest"}, test_id=tid(),
          claim="undocumented: verify the deleted posts are gone")
    posts = posts_in(g)
    ids_now = {p.get("id") for p in posts}
    for key in ("discussion_html", "discussion_text"):
        d = res.get(key) or {}
        if d.get("id") is None:
            print(f"verify {key}: no post id, nothing to delete")
            continue
        n = d["nonce"]
        gone = d["id"] not in ids_now and find_by(posts, n) is None
        print(f"verify {key}: id={d['id']} gone={gone}")


def split_stored(stored):
    """Segment of stored text per [NN] marker (sequential search); None if a marker is missing."""
    marks, pos = {}, 0
    for num in range(1, N_CASES + 1):
        mk = f"[{num:02d}]"
        i = stored.find(mk, pos)
        if i >= 0:
            marks[num] = i
            pos = i + len(mk)
    segs = {}
    for num in range(1, N_CASES + 1):
        if num not in marks:
            segs[num] = None
            continue
        start = marks[num] + len(f"[{num:02d}]")
        later = [v for v in marks.values() if v > marks[num]]
        seg = stored[start:min(later) if later else len(stored)]
        seg = re.sub(r"^(\s|<br\s*/?>)+", "", seg)
        seg = re.sub(r"(\s|<br\s*/?>)+$", "", seg)
        segs[num] = seg
    return segs


def tags_in(s):
    return {t.lower() for t in re.findall(r"<\/?([a-zA-Z][a-zA-Z0-9]*)", s)}


def strip_tags(s):
    return re.sub(r"<[^>]*>", "", s)


def verdict(inp, seg):
    """KEPT (identical) | CHANGED (shows how) | REMOVED (gone) | ESCAPED (shown as literal markup)."""
    if seg is None:
        return "REMOVED", "marker [NN] missing in stored content"
    i, s = inp.strip(), seg.strip()
    if s == i:
        return "KEPT", ""
    if s == "" and i:
        return "REMOVED", "nothing left"
    if s == i.replace("\n", "<br>"):
        return "CHANGED", "newline -> <br>"
    if strip_tags(i).strip() and not strip_tags(s).strip():
        return "REMOVED", f"text and markup gone, stored={s!r}"
    tg = tags_in(i)
    if tg and "&lt;" in s and not any(f"<{t}" in s.lower() for t in tg):
        return "ESCAPED", f"stored={s!r}"
    return "CHANGED", f"stored={s!r}"


def analyse(cases, res):
    cols = [("disc-html", "discussion_html"), ("disc-text", "discussion_text"), ("mail-html", "mail_html")]
    segs, verdicts = {}, {}
    for label, key in cols:
        d = res.get(key) or {}
        stored = d.get("content") or ""
        sg = split_stored(stored)
        if d.get("nonce"):
            if sg.get(1) is not None:
                sg[1] = sg[1].replace(d["nonce"], "").strip()
        segs[label] = sg
    table = []
    for num, text in cases:
        print(f"[{num:02d}] input: {text!r}")
        row = [f"{num:02d}"]
        for label, _ in cols:
            v, note = verdict(text, segs[label][num])
            seg = segs[label][num]
            print(f"      {label:9s}: {seg!r}  -> {v}" + (f" ({note})" if note and v != "KEPT" else ""))
            verdicts[(label, num)] = v
            row.append(v)
        table.append(row)
    print("\nNN | " + " | ".join(label for label, _ in cols))
    for row in table:
        print(" | ".join(row))
    for label, _ in cols:
        counts = {}
        for num, _ in cases:
            counts[verdicts[(label, num)]] = counts.get(verdicts[(label, num)], 0) + 1
        print(label, counts)


def run():
    cases = parse_cases()
    res = {}
    try:
        res["discussion_html"] = disc_send("html", cases)
        res["discussion_text"] = disc_send("text", cases)
        res["mail_html"] = mail_send(cases)
    finally:
        delete_and_verify(res)

    save_fixture(SEG, "discussion_html", res["discussion_html"], max_str=10 ** 7)
    save_fixture(SEG, "discussion_text", res["discussion_text"], max_str=10 ** 7)
    save_fixture(SEG, "mail_html", res["mail_html"], max_str=10 ** 7)
    print("created post ids:", [i for k, i in c.created if k == "post"],
          "| mail ids:", [i for k, i in c.created if k == "mail"])
    analyse(cases, res)


if __name__ == "__main__":
    run()
