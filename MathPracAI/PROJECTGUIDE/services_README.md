# Services

## Purpose

Services contain the business logic of MathPracAI. Each service represents an independent subsystem responsible for one area of the application.

## Responsibilities

- Coordinate workflows
- Implement business logic
- Communicate between subsystems
- Provide reusable functionality to routes

Current services include Firebase and Milo.

## Philosophy

Each service should own exactly one subsystem. Services should be independent and communicate through well-defined interfaces. Business logic should never be duplicated across multiple services.
