# 10_API_Design.md

# API Design

## POST /sessions/upload

Upload AI session.

Response:
200 OK

---

## GET /profile

Returns developer profile.

---

## GET /memories

Returns stored memories.

---

## POST /search

Semantic search.

Input

{
 "query":"FastAPI"
}

---

## GET /reports

Returns generated reports.

---

## Authentication

JWT Authentication

---

## Error Codes

400 Bad Request

401 Unauthorized

404 Not Found

500 Internal Server Error