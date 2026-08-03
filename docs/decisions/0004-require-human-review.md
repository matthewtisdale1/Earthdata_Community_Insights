# ADR 0004: Require human review for inferred relationships and implementation claims

- Status: Accepted
- Date: 2026-08-03

## Context

The platform will use automated methods to cluster evidence and propose relationships between community needs and implementation artifacts. These methods can surface useful candidates, but they can also create false matches or overstate what a ticket, pull request, release, or documentation page actually accomplishes.

A GitHub issue may be closed because it was implemented, duplicated, rejected, superseded, or abandoned. Artifact state alone is not enough to determine whether a community need has been solved.

## Decision

Treat automated clustering, scoring, and need-to-artifact matching as draft hypotheses. Require explicit human review before reporting an artifact as partially or fully addressing, implementing, or documenting a community need.

## Rationale

- Community evidence and implementation status can be ambiguous.
- Human reviewers can consider context that is absent from titles and ticket bodies.
- Review decisions provide an evaluation set for improving future matching methods.
- The approach reduces the risk of misleading program or investment conclusions.

## Consequences

Positive:

- Confirmed relationships are more trustworthy.
- Automated and reviewed records remain clearly distinguishable.
- Reviewer notes can explain edge cases and partial coverage.
- Match quality can be measured against reviewed decisions.

Tradeoffs:

- Review requires time and domain expertise.
- Candidate queues must be prioritized to avoid overwhelming reviewers.
- The application must preserve decision history and reviewer identity.

## Required behavior

- Store automated method, version, scores, and explanation.
- Store review status separately from relationship type.
- Preserve rejected candidates for evaluation unless governance requires deletion.
- Do not equate `closed` with `implemented`.
- Show pending matches separately from confirmed implementations.
- Record reviewer, timestamp, decision, and notes for confirmed or rejected relationships.
