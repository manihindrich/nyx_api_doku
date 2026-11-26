# Good practice

Recommendations from running an RSS bot on the API (2026-11) and from the tests in this repository. Every rule links to the test that backs it.

## Requests

- **Send booleans as `true` / `false`.** Other values give 422 or are silently ignored [T-rights-18, T-last-24].
- **Do not rely on errors to validate input.** Many invalid values return 200 with default behaviour ([Errors](11_errors.md#invalid-values-that-do-not-cause-an-error)).
- **Put `discussion/rights` parameters in the query string**, not in the body [T-rights-25].
- **Retry only temporary failures** (network errors, 5xx, 429) with exponential backoff. 400, 403, 404 and 422 do not change on retry. No 429 was seen at about one request per second.

## Errors

- **Handle both 401 shapes**: `{"error": true, "message": …}` and `{"error": {"code": 401, …}}` [T-notepad-08, T-rights-28].
- **A missing discussion is 400, not 404**: `Nepodařilo se načíst diskuzi.` [T-discussion-97]. A client that checks for 404 will treat a missing discussion as a temporary error.
- **Treat a missing field as `false` / `0`.** Flags and counters are omitted when unset ([Models](12_models.md#general-rules)).

## Writing posts and mail

- **Make every automated message unique**, e.g. with a timestamp. nyx rejects a text identical to the user's previous post or message [T-discussion-31, T-mail-22].
- **Find the new post's ID yourself.** `send/text` and `mail/send` return `{}`. Read back with `?user=<you>&order=newest` and match on the unique text [T-discussion-25, T-mail-16].
- **Upload attachments just before posting.** Every waiting file is attached to the next post in that discussion; old uploads you forgot about will be attached too [T-file-24…26].
- **Do not use `ar_*` flags to decide what you may do.** They were all `false` for the discussion owner [T-discussion-01]. Try the action and handle the error.

## Reading mail and posts

- **Poll with a cursor**: remember the highest ID and call `?order=newer_than&from_id=<id>` [T-mail-07]. Without `from_id`, `newer_than` silently returns the newest page instead [T-mail-09].
- **Pages have 20 items.** With `newer_than`, if 20 come back there may be more; continue from the highest ID.
- **Sort by ID yourself.** Every page is sorted newest first, even with `order=oldest` [T-mail-06, T-discussion-11].
- **Read links from `href`.** nyx turns URLs in incoming mail and posts into `<a>` elements and shows discussion links as `[name]` [HTML line 27, 28].
- **`username` in mail is always the other party**; use `incoming` to tell received from sent [T-mail-01].

## Rights

- **Call `rights/add` before `rights`** [T-rights-33, T-rights-38].
- **Remove rights from the top down**: `edit_rights`, `edit`, `delete`, `write`, `read`. A lower right cannot be removed while a higher one is set [T-rights-03, T-rights-48…52].

## Security

- **Keep the token out of code and URLs** ([Authentication](01_authentication.md)).
- **Public discussions are readable without a token** [T-discussion-99]. Anything posted there is public.

> [!CAUTION]
> **Not verified by tests:** whether more than 20 items are returned by `newer_than`, and any rate limit. The 20-item continuation rule above is a precaution.
