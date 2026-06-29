# API Style Guide

Standards for all REST APIs built at Acme Corp.

## URL Structure

```
https://api.acme.internal/v1/{resource}
```

- Use plural nouns for resources: `/users`, `/documents`.
- Nest sub-resources logically: `/documents/{id}/chunks`.
- Use kebab-case for multi-word resources: `/incident-reports`.

## HTTP Methods

| Method | Action | Idempotent |
|---|---|---|
| GET | Retrieve resource(s) | Yes |
| POST | Create resource | No |
| PUT | Full replace | Yes |
| PATCH | Partial update | No |
| DELETE | Remove resource | Yes |

## Pagination

All list endpoints must support cursor-based pagination:

```json
{
  "items": [...],
  "next_cursor": "eyJpZCI6IDEyM30="
}
```

Request with `?cursor=...&limit=100`. Default limit is 20, maximum is 200.

## Error Responses

Use consistent error envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "tags must be a comma-separated list",
    "details": {}
  }
}
```

Standard error codes:

| HTTP Status | Code | When |
|---|---|---|
| 400 | VALIDATION_ERROR | Malformed request |
| 401 | UNAUTHORIZED | Missing or invalid auth |
| 404 | NOT_FOUND | Resource doesn't exist |
| 409 | CONFLICT | Duplicate resource |
| 422 | UNPROCESSABLE_CONTENT | Parser failure |
| 429 | RATE_LIMITED | Too many requests |

## Versioning

- API version is in the URL path: `/v1/`.
- Breaking changes require a new version.
- Deprecate before removing: announce in changelog, keep for 3 months.
