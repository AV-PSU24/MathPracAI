# app.py

## Purpose

app.py is the application's entry point.

## Responsibilities

- Create the Flask application
- Load configuration
- Register blueprints
- Configure global application settings

## Philosophy

app.py should remain as small as possible.

It is not responsible for business logic, mathematical logic, AI tutoring, or database operations. If logic begins accumulating here, it almost certainly belongs in another subsystem. A small app.py makes the application easier to reason about and keeps startup behavior predictable.
