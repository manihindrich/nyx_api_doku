# Files

Uploading attachments for posts and mail.

| Method | Path | Purpose |
|---|---|---|
| `PUT` | `/api/file/upload` | Upload a file |
| `POST` | `/api/file/embed/{id}/{state}` | Show an image inline or as a link |
| `DELETE` | `/api/file/delete/{id}` | Delete an uploaded file |

Verification: live tests in [`tests/seg_file.py`](../tests/seg_file.py), 2026-11-27. All test files were deleted afterwards. Test IDs are in brackets, `F-` = `T-file-`.

---

## How attachments work

1. Upload the file with `file_type=discussion_attachment` and `id_specific=<discussion ID>` (or `mail_attachment` and `0`).
2. The file waits in `waiting_files`: in `discussion_common.waiting_files` of `GET /api/discussion/{id}`, or in `waiting_files` of `GET /api/mail` [F-22, -23].
3. The next post sent to that discussion gets all waiting files attached, and `waiting_files` becomes empty [F-24…26].

Attached images are added below the post text in `<div class='image-attachments'>`; other files as links in `<ul class=attachments>` [F-25].

> [!CAUTION]
> **Not tested:** attaching a file to a mail message. The tests did not send mail with a waiting attachment.

---

## PUT /api/file/upload

`multipart/form-data`:

| Field | Required | Values |
|---|---|---|
| `file` | yes | file content |
| `file_type` | yes | `discussion_attachment`, `discussion_backup`, `mail_attachment`, `mail_backup`, `free_file`, `market_attachment`, `event_attachment` |
| `id_specific` | yes | discussion ID for `discussion_*`, `0` otherwise |

```bash
curl -s -X PUT -H "Authorization: Bearer $NYX_API_TOKEN" \
  -F "file=@image.png;type=image/png" -F "file_type=discussion_attachment" -F "id_specific=100001" \
  https://nyx.cz/api/file/upload
```

**200** [F-01]

```json
{
  "id": 9000002, "file_type": "discussion_attachment", "id_specific": 100001, "id_specific2": null,
  "filename": "nyxapidoku-1207828a8b.png", "size": 69, "uploaded_at": "2026-11-27T00:15:10", "mimetype": "image/png",
  "image_width": 1, "image_height": 1, "image_avg_color_hex": "ff0000",
  "image_embed": true, "image_embed_option": "full",
  "url": "/files/000/000/9000002_00000000000000000001/original.png?name=nyxapidoku-1207828a8b.png",
  "thumb_url": "/files/000/000/9000002_00000000000000000001/square.jpg"
}
```

- `url` and `thumb_url` are relative to `https://nyx.cz`.
- All seven `file_type` values were accepted [F-01…07]. With `id_specific=0` the response has `"id_specific": null`.
- `market_attachment` and `event_attachment` converted a PNG to a JPEG [F-05, -06].
- `mimetype` is detected from the content, not from the declared type. GIF and PNG were recognised. A fake JPEG, a PDF and random bytes became `octet/stream`, with `image_embed: false`, `image_embed_option: "link"` and `thumb_url: null` [F-08…13].
- A 5 MB file was accepted [F-14]. No size limit was found.

| Case | Status | Body | Test |
|---|---|---|---|
| `file`, `file_type` or `id_specific` missing; `file_type=foo` | 422 | `{"error": true, "message": "422"}` | F-15…18 |
| `id_specific` of a discussion the user cannot edit (`999999999`) | 403 | `{"error": true, "code": "forbidden", "message": "Nemáte právo tohle upravovat."}` | F-19 |
| missing or invalid token | 401 | `{"error": {"code": 401, "reason": "Unauthorized", "description": "The request requires user authentication."}}` | F-20, -21 |

> [!WARNING]
> **Swagger says** `mimetype` is one of five values and that `thumb_url` is a string. In reality every type tried was accepted (PDF, ZIP, text, binary, up to 5 MB; unknown types become `octet/stream`), and `thumb_url` is `null` for non-images. The field `image_embed_option` is not documented.

Fixtures: [`upload_200.json`](../tests/fixtures/file/upload_200.json), [`waiting_files_example.json`](../tests/fixtures/file/waiting_files_example.json)

---

## POST /api/file/embed/{id}/{state}

`state=true` shows an image inline, `false` as a link.

```bash
curl -s -X POST -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/file/embed/9000002/false
```

**200** `{}` [F-27, -28]. `state=1` or `abc`: 422 [F-29, -30].

> [!CAUTION]
> **Not verified:** the visible effect of `embed` on the attached post. The tests only checked the responses.

---

## DELETE /api/file/delete/{id}

```bash
curl -s -X DELETE -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/file/delete/9000002
```

**200** `{}` [F-32]. Deleting the same file again also returns **200** `{}` [F-33].

Deleting the waiting mail attachment removed it from `waiting_files` of `GET /api/mail` [F-37, F-50].

> [!CAUTION]
> **Not tested:** deleting another user's file. The test harness only deletes files it uploaded.

Fixture: [`delete_200.json`](../tests/fixtures/file/delete_200.json)
