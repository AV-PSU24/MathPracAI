# Routes

## Purpose

Routes expose the backend to the frontend through HTTP endpoints.

## Responsibilities

- Receive HTTP requests
- Validate request data
- Call the appropriate service
- Return HTTP responses

## Philosophy

Routes should act only as translators between the frontend and the backend. They should never contain business logic. If a route becomes difficult to read, the logic belongs inside a service or the Math Engine.
