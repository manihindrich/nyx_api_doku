# Authentication

Base URL: `https://nyx.cz/api`

Every request is authenticated with a personal API token in the `Authorization` header:

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/notepad
```

All tests in this repository use this header [all segments].

## Getting a token

The API has no login endpoint. The token is created in the account settings on the nyx.cz website.

> [!CAUTION]
> **Not verified by tests:** how the token is created, whether it expires, and whether it can be revoked. These are website features, not API calls.

## Keep the token secret

- Store it outside the code (environment variable, `.env` file excluded from git).
- Do not put it into a URL. [`register_for_notifications`](08_notifications.md) is the only endpoint whose path contains a token.

## Requests without a valid token

| Endpoint | Missing token | Invalid token | Test |
|---|---|---|---|
| most `GET` endpoints | 401 `Authorization needed` | 401 `Invalid token` | T-notepad-07, -08 and others |
| `GET /api/discussion/{id}`, public discussion | **200**, full content | **200** | T-discussion-99, -100 |
| `GET /api/discussion/{id}`, non-public discussion | 400 `Přístup odmítnut.` | 400 `Přístup odmítnut.` | T-discussion-23, -24 |
| `POST /api/discussion/rights/add`, `PUT /api/file/upload`, `POST /api/register_for_notifications/…` | 401, long form | 401, long form | T-rights-28, T-file-20, T-notifications-10 |

The two 401 body shapes are described in [Errors](11_errors.md#401-unauthorized).

> [!WARNING]
> **Swagger says** nothing about authentication in its security schemes and lists no 401 response.
