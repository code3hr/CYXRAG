# Dummy Trade Service

Dummy Trade Service is a small example project for testing Open RAG against a
repository that is not Open RAG itself.

## Product behavior

The service manages trade approval for a fictional marketplace.

Trade approval has three steps:

1. validate that the buyer and seller exist,
2. check that the trade amount is inside the configured limit,
3. record an approval decision with an audit reason.

Rejected trades must include a user-visible reason and an internal audit reason.

## Ownership

- Trade approval logic lives in `src/trade_service.py`.
- Operational policy lives in `docs/policy.md`.
- Architecture notes live in `docs/architecture.md`.

## Runtime rule

This example is intentionally small. It should be answerable through retrieval
packets without requiring a model runtime.
