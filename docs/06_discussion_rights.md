# Discussion rights

Per-user access rights in a discussion. The caller must be allowed to manage rights (the tests used the discussion owner).

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/discussion/rights/add` | Add a user to the rights list |
| `POST` | `/api/discussion/rights` | Set one right of a user |
| `DELETE` | `/api/discussion/rights` | Remove a user from the rights list |

The API cannot list the users in the rights list.

Verification: live tests in [`tests/seg_rights.py`](../tests/seg_rights.py), 2026-11-25, on one user in discussion 100001. Test IDs are in brackets, `R-` = `T-rights-`.

> [!IMPORTANT]
> All parameters go in the **query string**. The same parameters in a form body return 422 [R-25, R-27].

---

## POST /api/discussion/rights/add

| Parameter | Required |
|---|---|
| `discussion_id` | yes |
| `username` | yes |

```bash
curl -s -X POST -H "Authorization: Bearer $NYX_API_TOKEN" \
  "https://nyx.cz/api/discussion/rights/add?discussion_id=100001&username=PEERUSER"
```

**200** `{}` [R-38]. A newly added user has `read` and `write` [R-39].

| Case | Status | Body | Test |
|---|---|---|---|
| user already in the list | 400 | `{"error": true, "message": "Uživatel již má uživatelská práva nastavená."}` | R-26 |

---

## POST /api/discussion/rights

| Parameter | Required | Values |
|---|---|---|
| `discussion_id` | yes | |
| `username` | see note | |
| `right` | yes | `read`, `write`, `delete`, `edit`, `edit_rights` |
| `set` | no | `true`, `false` |

```bash
curl -s -X POST -H "Authorization: Bearer $NYX_API_TOKEN" \
  "https://nyx.cz/api/discussion/rights?discussion_id=100001&username=PEERUSER&right=delete&set=true"
```

**200** returns the user's rights after the change [R-02]:

```json
{ "discussion_id": 100001, "ar_read": true, "ar_write": true, "ar_delete": true,
  "ar_edit": true, "ar_rights": true, "days_left": -1 }
```

`right=edit_rights` maps to `ar_rights` [R-11].

### The rights form a hierarchy

`read` < `write` < `delete` < `edit` < `edit_rights`

- A right **cannot be removed while a higher one is set**. The call returns 200, but nothing changes [R-03, -05, -07, -09].
- Remove rights from the top down [R-48…52].

### Values

| Input | Status | Body | Test |
|---|---|---|---|
| `set` missing | 200 | current rights (the effect could not be observed: the right was already set) | R-24 |
| `set=1`, `0`, `abc` | 422 | `{"error": true, "message": "422"}` | R-18, -19, -21 |
| `right=foo`, `right` missing | 422 | same | R-22, -23 |
| `right=grant_edit_rights`, `right=public` | 400 | `{"error": true, "message": "Nepodařilo se uložit práva."}` | R-13…16 |
| user not in the rights list | 400 | same | R-33 |

> [!NOTE]
> Call `rights/add` first. `rights` fails for a user who is not in the list.

> [!WARNING]
> **Swagger says** `right` also accepts `grant_edit_rights` and `public`, and that `set` is required. In reality, with a `username`, those two values always fail (without `username` not tested), and a missing `set` is accepted. Swagger's reference to `DiscussionGlobalRights` is broken: the schema is nested inside `DiscussionAccessRight` by mistake.

> [!CAUTION]
> **Not tested:** calling without `username`. Swagger says this changes the discussion's **global** rights (response `DiscussionGlobalRights`). The test harness does not allow it.

---

## DELETE /api/discussion/rights

| Parameter | Required |
|---|---|
| `discussion_id` | yes |
| `username` | yes |

```bash
curl -s -X DELETE -H "Authorization: Bearer $NYX_API_TOKEN" \
  "https://nyx.cz/api/discussion/rights?discussion_id=100001&username=PEERUSER"
```

**200** `{}`. Removes the user and all their rights [R-31, R-33].

| Case | Status | Body | Test |
|---|---|---|---|
| user not in the list | 400 | `{"error": true, "message": "Nepodařilo se uložit práva."}` | R-32 |

---

## Authentication errors

Missing or invalid token on `rights/add` returns 401 with a **different body shape** than elsewhere [R-28, R-29]:

```json
{ "error": { "code": 401, "reason": "Unauthorized", "description": "The request requires user authentication." } }
```

See [Errors](11_errors.md).

Fixtures: [`tests/fixtures/rights/`](../tests/fixtures/rights/)
