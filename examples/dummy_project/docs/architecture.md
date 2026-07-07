# Architecture

The dummy project has one application service.

`TradeService` owns trade approval decisions. It accepts a trade request, applies
the configured policy, and returns an approval result.

The service does not send payments. It only decides whether a trade can proceed.
Payment execution would belong to a separate payment adapter in a real project.

## Data flow

1. A caller submits buyer id, seller id, amount, and currency.
2. `TradeService` validates required participants.
3. `TradeService` checks policy limits.
4. The approval result is returned with a status and reason.

## Extension boundary

New payment rails should not be added to `TradeService`. Add a separate adapter
and keep trade approval independent from payment execution.
