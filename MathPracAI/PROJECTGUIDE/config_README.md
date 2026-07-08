# Config

## Purpose

The Config folder centralizes application configuration and environment loading.

## Responsibilities

- Load environment variables
- Provide shared configuration
- Configure application startup

## Philosophy

Configuration should exist in one predictable location. Secrets should never be hardcoded, and environment-specific settings should be loaded through configuration rather than scattered throughout the codebase.
