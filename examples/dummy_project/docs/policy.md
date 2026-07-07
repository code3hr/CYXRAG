# Trade Approval Policy

The maximum default trade amount is `1000`.

Approval rules:

- approve trades when buyer id and seller id are present,
- reject trades when buyer id or seller id is missing,
- reject trades when amount is less than or equal to zero,
- reject trades when amount is greater than the configured maximum.

Every rejection must include:

- `approved: false`
- a short public reason
- an audit reason that can be stored by the caller

The policy is intentionally deterministic so tests and retrieval examples can
verify behavior without calling a model.
