# Security

Open RAG is designed for local/offline retrieval and should not upload source content
to networked services by default.

## Reporting a security issue

If you discover a security issue:

1. Open a private report with your project contact.
2. Include:
   - command/output and reproduction steps
   - impacted files (if any)
   - severity and risk summary
   - proof-of-concept details

## Scope

- Validate local runtime endpoints are configured to localhost only when possible.
- Avoid logging sensitive source text or secrets in packets/debug output.
- Keep model runtime calls explicit and opt-in.

## Response expectations

- Confirm receipt of report.
- Triaging within a few business days.
- Security fixes are prioritized before non-security feature work.
