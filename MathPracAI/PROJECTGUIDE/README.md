# MathPracAI Project Guide

## Purpose

Welcome to the MathPracAI developer guide.

This folder documents the purpose and architectural philosophy of each major subsystem in the project.

Rather than maintaining one massive documentation file, each major folder has its own README describing:

- Purpose
- Responsibilities
- Philosophy

## Responsibilities

The PROJECTGUIDE folder serves as the central architectural handbook for MathPracAI.

Its purpose is to help future developers and future Codex sessions quickly understand how the project is organized and why it is structured that way.

## Philosophy

The documentation should describe architectural intent rather than implementation details.

Every subsystem should have a clearly defined responsibility and a corresponding README explaining its role within the project.

Core Design Principles

1. Mathematical correctness comes first.
2. Every subsystem has one responsibility.
3. The canonical Problem object is the source of truth.
4. Keep business logic isolated.
5. Prefer readability over cleverness.
6. Never duplicate mathematical logic.
7. Build systems that scale rather than patching edge cases.
