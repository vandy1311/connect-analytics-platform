# Product Overview

JWO Prepaid Card Authorization Service — an entry gate balance-check system for Just Walk Out (JWO) retail stores.

## What It Does

When a customer presents a prepaid card at a store entry gate, the service:
1. Identifies the card as prepaid via BIN lookup
2. Queries the payment processor for available balance (with preauth)
3. Compares balance against a configurable store threshold (`multiplier × average_basket_size`)
4. Approves or denies entry, opening/closing the gate accordingly
5. Reverses preauth immediately on denial

## Phase 1 Scope (MVP — target Dec 2026)

- Entry gate balance check only (no in-store monitoring)
- US ptech locations only
- Single payment processor
- Threshold-based approval/denial with per-store configuration
- PCI-DSS compliant logging (no full card numbers, no CVV, no expiry)
- Default config: 3× multiplier, $50 average basket → $150 required balance

## Key Business Rules

- Denied customers can retry immediately with a different card (no cooldown)
- Preauth reversal must happen within seconds of denial
- Config changes propagate within 5 minutes (in-memory cache with TTL)
- If store config is missing, use defaults and alert ops
- Fail-safe: deny entry on processor errors, timeouts, or missing balance data

## Success Metrics

- Prepaid entry approval rate: ≥60–70%
- Payment completion rate (approved entry → successful exit payment): ≥85%
- Authorization latency (p95): <1500ms
- System uptime: no degradation from current JWO gate performance
