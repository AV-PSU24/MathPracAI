# LLM

## Purpose

The LLM package isolates communication with external language models from the rest of the application.

## Responsibilities

- Connect to AI providers
- Execute requests
- Handle provider errors
- Manage provider-specific configuration

## Philosophy

MathPracAI should never depend on a specific AI provider. The rest of the application should communicate only with this package, allowing Gemini or any future provider to be replaced without affecting the rest of the system.
