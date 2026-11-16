# ADR-0001: Keep CampusFlow synthetic-only until school review

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

The current app handles student names and marks in school-scoped API endpoints. Passing local tests does not establish legal basis, guardian notice, production security, data residency, retention, or recovery suitability for real educational records.

## Decision

Keep the public demo and test data synthetic. Do not import real student records until an owner-approved school data agreement, qualified privacy review, managed PostgreSQL, tested encrypted backup/restore, monitoring, support contact, retention/deletion rules, and production access review are complete.

## Consequences

- Public examples, screenshots, and demos must remain fictional.
- A product or health endpoint may not reveal student data.
- A paid pilot can begin only after the school and owner approve scope, responsibilities, security terms, and incident handling.
