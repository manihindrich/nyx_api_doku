# HTML in posts and mail

What nyx does with the content of posts ([`send/text`](05_discussion.md#post-apidiscussiondiscussionidsendtext)) and mail ([`mail/send`](04_mail.md#post-apimailsend)).

Verification: [`tests/seg_html.py`](../tests/seg_html.py), 2026-11-27. One document with 34 numbered test lines was sent as a post with `format=html`, as a post with `format=text`, and as mail with `format=html`. The stored `content` was read back through the API. Fixtures: [`tests/fixtures/html/`](../tests/fixtures/html/).

> [!NOTE]
> The tests show the **stored** HTML returned by the API. How a browser or a mobile client renders it was not tested.

## `format=html`

Posts and mail behave **identically** [all 34 lines].

### Kept as sent

| Input | Line |
|---|---|
| `<b>`, `<i>`, `<u>`, `<s>` | 01–04 |
| `<font color="red">`, `<font size="1">` | 08, 09 |
| `<center>`, `<small>`, `<h2>`, `<hr>`, `<br>` | 10, 12–15 |
| `<pre>` (spaces kept) | 11 |
| `<xmp>` | 19 |
| `<span style="color:red">` (the `style` attribute stays) | 29 |
| `<ul><li>`, `<blockquote>` | 31, 32 |
| `&lt;` `&gt;` `&amp;` | 33 |

### Changed

| Input | Stored | Line |
|---|---|---|
| `<a href="https://example.com">` | `rel="noopener noreferrer"` added; `target` and `title` kept | 05, 06, 25, 26 |
| `<img src="…" width="16">` | `width` dropped; `data-thumb` and `data-full-size` added | 07 |
| `<code>x = 1</code>` | `<div class="code"><pre style="background-color:#272822">` with coloured `<span>`s | 16 |
| ```` ```txt ```` fenced block | same code block | 18 |
| `<div class='spoiler'>` | `<div class="spoiler">` (quotes normalised) | 17 |
| `<table><tr>` | `<tbody>` added | 30 |
| bare URL `https://example.com/path` | `<a class="extlink" href="…">…</a>` | 27 |
| nyx discussion URL `https://nyx.cz/discussion/18379` | `<a href="/discussion/18379">[nyx :: API]</a>` | 28 |
| newline `\n` | `<br>` | 34 |

### Removed

| Input | Stored | Line |
|---|---|---|
| `<script>…</script>`, `<style>…</style>`, `<iframe>…</iframe>` | removed **with their content** | 20–22 |
| `onclick="…"` | attribute removed, tag kept | 23 |
| `href="javascript:…"` | `href` removed, `<a>` kept | 24 |

## `format=text`

- All markup is escaped and shown as text: `<b>` becomes `&lt;b&gt;` [lines 01–32].
- Entities are escaped again: `&lt;` becomes `&amp;lt;` [line 33].
- Bare URLs and nyx discussion URLs are still turned into links [lines 27, 28].
- `\n` becomes `<br>` [line 34].

## Practical rules

1. Use `format=html` when you send markup; use `format=text` for user input you want shown literally.
2. Use either `\n` or `<br>`, not both: every `\n` becomes `<br>`, so `<br>\n` gives two line breaks.
3. nyx converts URLs to links by itself, and replaces a nyx discussion URL with the discussion's name [lines 27, 28]. To show a discussion reference as plain text, write its ID instead of the URL.
4. For a monochrome code block use ```` ```txt ````. `<code>` is always a block, never inline.
5. Scripts, styles, iframes, event handlers and `javascript:` links are removed. You do not need to sanitise them yourself for nyx, but do not rely on this for other output.
6. When reading incoming content, links are `<a href=…>`; take the URL from `href`, not from the link text (discussion links show `[name]`).

> [!NOTE]
> An earlier observation in the nyx-rss project (2026-11-24) found that a URL inside a `title` attribute broke the HTML. In this test it was kept intact [line 25]. The case is unresolved; avoid URLs in `title`.

> [!CAUTION]
> **Not verified:** maximum length of formatted content (a 20 000-character plain post was accepted, see [Discussion](05_discussion.md)), and `format=markdown` beyond the fact that it is stored unconverted.
