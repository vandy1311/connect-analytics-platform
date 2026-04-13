# JWO Prepaid Balance Check - Phase 1 PRD

**Product Requirements Document (Word-Ready)**

**Version**: 1.0  
**Date**: March 16, 2026  
**Project**: JWO Prepaid Card Balance Check for Just Walk Out Stores  
**Phase**: Phase 1 MVP (December 31, 2026 Target)  
**Approach**: Option C - Phased Development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Overview](#product-overview)
3. [Scope Definition](#scope-definition)
4. [Functional Requirements](#functional-requirements)
5. [Non-Functional Requirements](#non-functional-requirements)
6. [Business Requirements](#business-requirements)
7. [Success Metrics](#success-metrics)
8. [Roadmap](#roadmap)
9. [Glossary](#glossary)

---

## Executive Summary

### Problem Statement

Just Walk Out (JWO) technology enables customers to enter a store, pick up items, and leave without waiting in a checkout line. Payment is automatically processed as customers exit. Currently, prepaid card customers are blocked from entering JWO locations to minimize the risk of payment declines when customers have insufficient funds to complete their purchase.

This blocking creates a poor customer experience for shoppers who use prepaid cards with sufficient funds to shop but are denied entry.

### Solution Overview

The JWO Prepaid Balance Check feature enables prepaid card customers to enter JWO stores if they have sufficient available balance to cover a configurable multiple of the store's average basket size. By requesting the available remaining balance during the entry preauthorization call, the system can make an informed decision about whether the customer has sufficient funds to complete their shopping experience.

### Phase 1 Scope

Phase 1 MVP focuses on the entry gate balance check feature with these characteristics:

- **Scope**: Entry gate balance check only
- **Threshold Logic**: Multiplier × Average Basket Size
- **Geographic Coverage**: US ptech locations
- **Payment Processor**: Single processor
- **Target Launch**: December 31, 2026
- **Key Benefit**: Expand customer access while managing payment risk

### Phase 2 (Future Enhancement)

Phase 2 will add advanced features:
- Payment guarantee requirements
- Real-time balance monitoring during shopping
- Multi-processor support
- Global deployment
- Mobile app integration

---

## Product Overview

### Vision

Enable prepaid card customers to enter JWO stores confidently, knowing their available balance has been verified, while reducing payment decline risk for Amazon and improving customer experience.

### Key Features (Phase 1)

1. **Prepaid Card Detection**: Identify prepaid cards via BIN lookup at entry gate
2. **Balance Verification**: Query available balance from payment processor
3. **Threshold Check**: Compare balance against store-specific threshold
4. **Entry Approval/Denial**: Binary decision with clear customer messaging
5. **Preauth Reversal**: Immediately void preauth if customer denied entry
6. **Store Configuration**: Allow per-store customization of threshold settings
7. **Error Handling**: Graceful handling of timeouts, missing balances, and config errors
8. **Logging & Monitoring**: Comprehensive logging for compliance and analytics

### Target Customers

- **Primary**: Prepaid card customers (retail customers, Amazon FC employees)
- **Secondary**: Store operations managers (configuration)
- **Tertiary**: Product/Finance teams (analytics and monitoring)

---

## Scope Definition

### Phase 1 In-Scope

| Feature | Details | Status |
|---------|---------|--------|
| Prepaid Card Detection | BIN lookup at entry gate | ✅ In Scope |
| Balance Query | Request available balance from processor | ✅ In Scope |
| Threshold Calculation | Multiplier × Average Basket | ✅ In Scope |
| Entry Approval | Display approval, open gate | ✅ In Scope |
| Entry Denial | Display denial message, allow retry | ✅ In Scope |
| Preauth Reversal | Void preauth within seconds | ✅ In Scope |
| Configuration Service | Per-store threshold settings | ✅ In Scope |
| Error Handling | Timeout, missing balance, missing config | ✅ In Scope |
| Logging | 2-year retention, PCI-compliant | ✅ In Scope |
| Real-Time Dashboard | 5-minute lag ops monitoring | ✅ In Scope |
| Supported Networks | Visa, Mastercard, Amex, Discover | ✅ In Scope |
| Geographic Coverage | US ptech locations | ✅ In Scope |

### Phase 1 Out-of-Scope

| Feature | Reason | Phase |
|---------|--------|-------|
| Real-Time Balance Monitoring | Monitor during shopping | Phase 2 |
| Payment Guarantee Requirement | Backup payment method | Phase 2 |
| Partial Transaction Support | Split payments | Phase 2 |
| Multi-Processor Integration | Multiple processors | Phase 2 |
| Global Deployment | Non-US regions | Phase 2 |
| Mobile App Integration | App notifications/features | Phase 2 |
| Fraud Detection | Advanced risk scoring | Phase 2 |
| Gift Cards | Non-network branded | Phase 2 |

---

## Functional Requirements

### FR-1: Prepaid Card Detection via BIN Lookup

**Description**: Identify prepaid cards at entry gate using BIN database lookup

**Details**:
- Initiate BIN lookup immediately on card presentation
- Query payment processor for card classification
- Support: Visa, Mastercard, American Express, Discover branded prepaid cards
- Non-supported cards handled gracefully with denial message

**Acceptance Criteria**:
- Card presented → BIN lookup completes <1 second
- Prepaid classification accuracy >95%
- Non-supported cards handled without system errors

---

### FR-2: Balance Query & Threshold Check

**Description**: Request balance and compare against store threshold

**Details**:
- Request available remaining balance with preauth
- Retrieve store-level config (threshold multiplier, average basket size)
- Calculate required balance: `threshold_multiplier × average_basket_size`
- Decision logic:
  - IF `available_balance ≥ required_balance` → APPROVE entry
  - ELSE → DENY entry

**Configuration Defaults**:
- Threshold Multiplier: 3X (customers need 3× average basket)
- Average Basket Size: $50

**Example**:
- Store config: 3X multiplier, $50 average basket
- Required balance: $150
- Available: $175 → ✅ APPROVED
- Available: $125 → ❌ DENIED

**Acceptance Criteria**:
- Threshold calculation correct
- Configuration changes take effect within 5 minutes
- Decision time <1 second

---

### FR-3: Entry Approval & Gate Operation

**Description**: Display approval and open gate automatically

**Details**:
- Display green approval indicator on entry gate display
- Gate opens automatically within 1-2 seconds
- Log entry data for compliance

**Logged Data**:
- Timestamp, store ID, card network
- Card last 4 digits (tokenized only)
- Available balance, threshold multiplier used
- Entry result

---

### FR-4: Entry Denial & Customer Communication

**Description**: Clearly deny entry and allow customer retry

**Details**:
- Gate remains closed
- Display message: "Insufficient funds available on card. Please use a different payment method."
- Immediately void preauth
- Customer can immediately retry with different card
- No cooldown period between attempts
- Support unlimited retries

**Logged Data**:
- Timestamp, store ID, card last 4 digits (tokenized)
- Available balance, required balance
- Denial reason

---

### FR-5: Preauth Reversal

**Description**: Reverse authorization when customer denied entry

**Details**:
- Trigger reversal within seconds of denial
- Funds returned per issuer timeline (typically 48 hours)
- Log reversal for audit

---

### FR-6: Store Configuration Service

**Description**: Allow per-store customization of threshold settings

**Details**:
- Per-store configuration:
  - `threshold_multiplier` (2X, 3X, 4X, etc.) - default: 3X
  - `average_basket_size` (dollars) - default: $50
- Changes take effect within 5 minutes
- Graceful defaults if config missing
- Alert operations team for missing configs

---

### FR-7: Error Handling - Authorization Timeout

**Description**: Handle bank timeout gracefully

**Details**:
- If preauth times out per provider SLA:
  - **Action**: Deny entry
  - **Message**: "Payment authorization timed out. Please try again or use a different payment method."
  - **Log**: Timeout event

---

### FR-8: Error Handling - Balance Not Returned

**Description**: Handle missing balance response (fail-safe)

**Details**:
- If preauth approved but no balance returned:
  - **Action**: Deny entry (cannot verify funds)
  - **Message**: "Unable to verify card balance. Please use a different payment method."
  - **Log**: Event for investigation

---

### FR-9: Error Handling - Missing Configuration

**Description**: Handle missing store configuration gracefully

**Details**:
- If store config missing:
  - **Action**: Use defaults (3X multiplier, $50 basket)
  - **Alert**: Send alert to operations team
  - **Log**: Missing config event
  - **Benefit**: Prevents store outage

---

## Non-Functional Requirements

### NFR-1: Authorization Latency

**Requirement**: Keep authorization within operational limits

**Specification**:
- Preauth request to balance return: <1 second
- Threshold calculation: <1 second
- Total entry decision: <1-2 seconds
- Gate opening latency: <1-2 seconds
- Target: No degradation of current JWO gate performance

**Priority**: Critical

---

### NFR-2: Availability & Reliability

**Requirement**: Maintain store operations availability

**Specification**:
- Minimize gate downtime
- Fail-safe approach: Deny entry if processor unavailable
- Graceful degradation (no system crashes)
- Support brief outages without manual intervention

**Priority**: Critical

---

### NFR-3: PCI-DSS Compliance

**Requirement**: Full PCI-DSS compliance for payment card data

**Specification**:
- NO full card number storage (tokenize only)
- Encrypted transmission (TLS 1.2+)
- Card masking in logs/displays (last 4 digits, tokenized)
- Access controls (role-based permissions)
- Audit logging (immutable records)
- Security assessments per processor requirements

**Priority**: Critical (Non-Negotiable)

---

### NFR-4: Geographic Scope

**Requirement**: Phase 1 MVP covers US ptech operations

**Specification**:
- Coverage: All ptech JWO locations in United States
- Single payment processor
- US data center
- Phase 2: Expand to other regions

**Priority**: Medium

---

### NFR-5: Data Retention & Logging

**Requirement**: Retain transaction data for compliance and analytics

**Specification**:
- **Retention**: 2 years minimum
- **Entry Attempt Data**: Timestamp, store ID, card network, last 4 (hashed), result
- **Balance Data**: Available balance, required balance, threshold used, pass/fail
- **Storage**: PCI-compliant data warehouse
- **Access**: SQL queries for authorized teams

**Priority**: High

---

## Business Requirements

### BR-1: Success Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Prepaid Entry Approval Rate | ≥60-70% | Enable access for qualifying customers |
| Payment Completion Rate | ≥85% | Reduce payment declines at exit |
| System Uptime | No degradation | Maintain current JWO reliability |
| Customer Experience | Deny message clear | Easy retry mechanism |

---

### BR-2: Stakeholder Alignment

| Stakeholder | Interest | Success Criteria |
|-------------|----------|------------------|
| **Customers** | Access, no friction | Quick approval/retry, clear messages |
| **Store Operations** | Revenue, customer flow | Minimal gate latency, reliable system |
| **Finance** | Risk reduction | Reduced payment declines, nonpayments |
| **Product** | Feature launch | On-time delivery, meeting targets |

---

### BR-3: Configuration Strategy

**Default Values**:
- Threshold Multiplier: 3X
- Average Basket Size: $50
- Implies: Customer needs $150 available for entry

**Store-Specific Configuration**:
- Product managers can adjust per store
- Based on historical basket data
- Changes propagate within 5 minutes

---

## Success Metrics

### Phase 1 Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Prepaid Customer Approval Rate | ≥65% | % of prepaid attempts approved |
| Payment Success Rate | ≥85% | % of approved → successful payment at exit |
| System Availability | >99% | Uptime of entry gate auth system |
| Entry Latency (p95) | <1.5 seconds | Time from card presentation to gate open |
| Error Rate | <1% | Failed transactions / total |
| Configuration Update Time | <5 minutes | New settings→propagated |

### Phase 1 Success Criteria

✅ **Prepaid Access Enabled**: Customers with sufficient balance can enter stores  
✅ **Risk Managed**: Payment decline rate reduced by leveraging balance threshold  
✅ **Reliable**: System uptime meets operational requirements  
✅ **Compliant**: PCI-DSS compliance verified  
✅ **Measurable**: Real-time dashboard + logging enable analytics

---

## Roadmap

### Phase 1 Timeline (MVP)

| Milestone | Target Date | Scope |
|-----------|-------------|-------|
| Requirements Approval | March 2026 | Finalize Phase 1 specs |
| Design Complete | April 2026 | Architecture, service design |
| Development Sprint 1 | May 2026 | Core balance check feature |
| Development Sprint 2 | June 2026 | Configuration service, error handling |
| Testing & QA | July-September 2026 | Unit, integration, production testing |
| Pilot (1-2 stores) | October 2026 | Real-world validation |
| Production Launch | December 2026 | Full US ptech rollout |

### Phase 2 Planning (Post-MVP)

| Feature | Target | Description |
|---------|--------|-------------|
| Payment Guarantees | Q1 2027 | Require backup payment method |
| Real-Time Monitoring | Q1/Q2 2027 | Monitor balance during shopping |
| Multi-Processor | Q2 2027 | Support Stripe, Square, Adyen, etc. |
| Global Deployment | Q2/Q3 2027 | Expand to international locations |
| Mobile App Integration | Q3 2027 | App-based balance visibility & alerts |

---

## Technical Specifications

### Architecture Overview

**Phase 1 Components**:

1. **Entry Gate Interface**
   - Card reader integration
   - Display system (approval/denial messages)
   - Gate control (open/close logic)

2. **Authorization Service**
   - BIN lookup for prepaid detection
   - Balance query orchestration
   - Threshold calculation
   - Approval/denial decision logic

3. **Configuration Service**
   - Store-level settings (threshold, basket size)
   - Default value management
   - Change propagation (<5 min)

4. **Logging & Monitoring Service**
   - Entry events
   - Balance data
   - Error events
   - Real-time dashboard

5. **Payment Processor Integration**
   - Preauth request/response handling
   - Balance query API calls
   - Reversal processing

### Supported Card Networks

- Visa (prepaid)
- Mastercard (prepaid)
- American Express (prepaid)
- Discover (prepaid)

### Technological Assumptions

- Single payment processor (Phase 1)
- US data center hosting
- Cloud-agnostic architecture (AWS/Azure/GCP compatible)
- RESTful APIs for integrations
- Event-driven logging

---

## Implementation Dependencies

### External Dependencies

1. **Payment Processor**
   - Balance query capability in preauth API
   - Reversal/void functionality
   - SLA commitments

2. **Existing JWO Systems**
   - Entry gate hardware/firmware
   - Gate display system
   - Configuration management system
   - Logging/data warehouse access

3. **Card Networks**
   - BIN database access
   - Card classification support

### Internal Dependencies

- Finance/Risk team sign-off on risk model
- Operations team support for configuration management
- Security team PCI-DSS compliance verification
- Product team for Phase 2 planning

---

## Assumptions & Constraints

### Assumptions

- Payment processor supports balance return in preauth response
- BIN database may have rare misclassifications (<5%)
- Store operations team will manage configuration updates
- Historical basket size data available for initial config

### Constraints

- Phase 1 limited to US ptech locations
- Single processor (reduces complexity)
- Prepaid cards only (not credit/debit)
- Entry gate decision only (not shopping monitoring)

---

## Glossary

| Term | Definition |
|------|-----------|
| **BIN** | Bank Identification Number - identifies card issuer and type |
| **Preauth** | Payment authorization hold before actual settlement |
| **Threshold** | Required available balance (multiplier × average basket) |
| **Reversal** | Void/cancel preauth to release held funds |
| **Tokenization** | Replace sensitive data with non-sensitive token |
| **Fail-Safe** | Deny rather than risk approval if uncertain |
| **JWO** | Just Walk Out - Amazon's cashierless store technology |
| **Ptech** | Physical technology stores (Amazon's flagship JWO locations) |
| **PCI-DSS** | Payment Card Industry Data Security Standard |

---

## Appendices

### A. Configuration Parameter Reference

**Store Settings** (per-location):

```
threshold_multiplier: 2X | 3X | 4X | Custom
average_basket_size: $XXX
default_threshold_multiplier: 3X
default_average_basket_size: $50
config_update_latency: <5 minutes
```

### B. Error Messages Reference

| Scenario | Customer Message |
|----------|-----------------|
| Approved | Green indicator displayed, gate opens |
| Insufficient Funds | "Insufficient funds available on card. Please use a different payment method." |
| Timeout | "Payment authorization timed out. Please try again or use a different payment method." |
| Balance Unavailable | "Unable to verify card balance. Please use a different payment method." |

### C. Logging Fields Reference

| Entry | Fields |
|-------|--------|
| Entry Attempt | timestamp, store_id, card_network, card_last4_hashed, available_balance, required_balance, decision_result |
| Approval | timestamp, store_id, card_last4_hashed, available_balance, threshold_multiplier_used |
| Denial | timestamp, store_id, card_last4_hashed, available_balance, required_balance, denial_reason |
| Error | timestamp, store_id, error_type, error_detail, card_last4_hashed |

---

**Document Version**: 1.0  
**Last Updated**: March 16, 2026  
**Status**: Approved for Construction  
**Next Review**: Post-Phase-1 Launch Analysis

