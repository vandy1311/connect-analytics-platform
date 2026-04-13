# JWO Prepaid Card Solution - Phase 1 Requirements Specification

**Document Status**: APPROVED - OPTION C PHASED APPROACH  
**Phase**: INCEPTION - Requirements Analysis  
**Date**: 2026-03-16  
**Project**: JWO Prepaid Balance Check for Just Walk Out Stores  
**Approved Scope**: Phase 1 MVP (BRD-Aligned)

---

## Executive Summary

**Phased Approach Decision**: After comparing the comprehensive AIDLC requirements with the approved JWO Prepaid Balance Check BRD (Dec 2025), we are implementing **Option C: Phased Approach**.

**Phase 1 (MVP)**: Follow BRD scope exactly
- Entry gate balance check only
- Simple threshold logic (multiplier × average basket)
- US-only deployment
- Single payment processor
- Standard JWO payment decline process
- Target: December 31, 2026

**Phase 2 (Enhancement)**: Add AIDLC enhancements
- Payment guarantee requirements
- Real-time balance monitoring
- Multi-processor support
- Global deployment
- Target: Q1/Q2 2027

This document specifies **Phase 1 requirements only**. Phase 2 will have separate requirements document.

---

## Intent Analysis

### Request Summary
Enable prepaid card customers to enter JWO stores if they have sufficient available balance to cover a configurable multiple of the store's average basket size, reducing payment decline risk while expanding customer access.

### Request Type
New Feature - Entry Gate Enhancement

### Scope Estimate
**Phase 1**: Single component (entry gate balance check)  
**Full solution**: Multiple components (future phases)

### Complexity Estimate
**Phase 1**: Moderate - Payment processor integration, threshold logic, configuration service  

---

## Phase 1 Functional Requirements

### FR-1: Prepaid Card Detection via BIN Lookup

**Requirement**: Identify prepaid cards at entry gate using BIN (Bank Identification Number) database lookup.

**Details**:
- Initiate BIN lookup immediately on card presentation at entry gate
- Query payment processor for card classification
- Support: Visa, Mastercard, American Express, Discover branded prepaid cards
- Non-network prepaid cards (e.g., store gift cards) are not supported

**Acceptance Criteria**:
- Card presented → BIN lookup completes <1 second
- Prepaid classification accurate >95%
- Non-supported cards handled gracefully (denial with message)

**Priority**: Critical

---

### FR-2: Balance Query & Threshold Check

**Requirement**: Query available balance and compare against store threshold to determine entry approval.

**Details**:
- Request available remaining balance from payment processor with preauth
- Retrieve store-level configuration:
  - `threshold_multiplier` (default: 3X, examples: 2X, 3X, 4X)
  - `average_basket_size` (default: $50)
- Calculate required balance: `threshold_multiplier × average_basket_size`
- **ALLOW entry IF**: `available_balance ≥ required_balance`
- **DENY entry IF**: `available_balance < required_balance`

**Examples**:
- Store config: 3X multiplier, $50 average basket
- Required balance: 3 × $50 = $150
- Available balance: $175 → APPROVED
- Available balance: $125 → DENIED

**Acceptance Criteria**:
- Threshold calculation correct
- Configuration changes take effect within 5 minutes
- Decision time <1 second (from balance query to decision)

**Priority**: Critical

---

### FR-3: Entry Approval Display & Gate Operation

**Requirement**: Provide clear approval indication and automatic gate opening for qualifying customers.

**Details**:
- Display green approval indicator on entry gate display
- Gate opens automatically within 1-2 seconds
- Log: timestamp, store ID, card network, last 4 digits (tokenized), available balance, threshold multiplier used

**Acceptance Criteria**:
- Green indicator displays correctly
- Gate opening latency <1-2 seconds
- Logging captures all required fields
- No full card numbers in logs (PCI compliance)

**Priority**: Critical

---

### FR-4: Entry Denial with Customer Communication

**Requirement**: Clearly communicate denial reason and allow customer to retry with different payment method.

**Details**:

**On Entry Denial**:
- Gate remains closed
- Display message (customer-friendly): "Insufficient funds available on card. Please use a different payment method."
- Immediately void/reverse preauth to release customer funds
- Log: timestamp, store ID, last 4 digits (tokenized), available_balance, required_balance

**Retry Mechanism**:
- Customer can immediately present different card at same reader
- No cooldown period between attempts
- Support unlimited retries

**Acceptance Criteria**:
- Message displays clearly and is customer-friendly
- Preauth reversal completes within seconds
- Multiple payment attempts work without errors
- Denial logged correctly

**Priority**: Critical

---

### FR-5: Preauth Reversal Handling

**Requirement**: Immediately reverse preauthorization when customer denied entry.

**Details**:
- Trigger reversal within seconds of denial
- Funds returned to customer per issuer timeline (typically 48 hours)
- Log reversal for compliance/audit
- Support reversal for all supported card networks

**Priority**: Critical

---

### FR-6: Store Configuration Service

**Requirement**: Allow product managers to configure threshold settings per store location.

**Details**:
- Per-store configuration parameters:
  - `threshold_multiplier` (e.g., 2X, 3X, 4X) - default: 3X
  - `average_basket_size` (in dollars) - default: $50
- Configuration changes take effect within 5 minutes
- Graceful defaults: If config missing, use defaults automatically
- Alert operations team when defaults are used

**Acceptance Criteria**:
- Configuration UI/API allows per-store settings
- Changes propagate within 5 minutes
- Defaults used without system crash
- Operations alert sent for missing configs

**Priority**: High

---

### FR-7: Error Handling - Timeout

**Requirement**: Handle bank authorization timeout gracefully.

**Details**:
- If preauth request times out per payment provider SLA:
  - **Action**: Deny entry
  - **Message**: "Payment authorization timed out. Please try again or use a different payment method."
  - **Logging**: Log timeout event with card last 4 (tokenized), store ID

**Priority**: High

---

### FR-8: Error Handling - Balance Not Returned

**Requirement**: Handle cases where bank approves preauth but does not return balance.

**Details**:
- If preauth approved but NO available balance returned:
  - **Action**: Deny entry (fail-safe approach - cannot verify funds)
  - **Message**: "Unable to verify card balance. Please use a different payment method."
  - **Logging**: Log event for investigation
- **Rationale**: Rare case indicating processor compatibility issue; prefer safe denial over risk

**Priority**: High

---

### FR-9: Error Handling - Missing Configuration

**Requirement**: Handle missing or invalid store configuration gracefully.

**Details**:
- If store configuration (threshold, basket size) missing/invalid:
  - **Action**: Use default values (3X multiplier, $50 basket)
  - **Alert**: Send to operations team (config admin issue)
  - **Logging**: Log the missing config event
- **Rationale**: Prevents store outage due to admin errors

**Priority**: High

---

## Phase 1 Non-Functional Requirements

### NFR-1: Entry Authorization Latency

**Requirement**: Keep entry authorization within acceptable operational parameters.

**Details**:
- Preauth request to balance return: <1 second
- Threshold calculation: <1 second  
- Total entry decision time: <1-2 seconds
- Gate opening latency: <1-2 seconds
- **Target**: Do not degrade current JWO gate performance

**Priority**: Critical

---

### NFR-2: Availability & Reliability

**Requirement**: Maintain acceptable store operation availability.

**Details**:
- Minimize gate downtime for missing payment processor
- Fail-safe approach: Deny entry if processor unavailable
- Do not crash system; gracefully degrade
- Support brief outages without manual intervention

**Priority**: Critical

---

### NFR-3: PCI-DSS Compliance

**Requirement**: Maintain full PCI-DSS compliance for payment card handling.

**Details**:
- **NO full card number storage** - tokenize only
- **Encrypted transmission** of all card data (TLS 1.2+)
- **Card masking** in logs/displays - last 4 digits only (tokenized)
- **Access controls** - role-based permissions
- **Audit logging** - immutable logs of all card interactions
- **Security assessments** - per payment processor requirements

**Priority**: Critical (Non-Negotiable)

---

### NFR-4: Geographic Scope - Phase 1

**Requirement**: Focus Phase 1 MVP on US ptech operations.

**Details**:
- **Coverage**: All ptech JWO locations in United States
- **Payment Processor**: Single (primary processor for Phase 1)
- **Data Residency**: US data center
- **Phase 2**: Expand to alternate processors and other regions

**Priority**: Medium

---

### NFR-5: Data Retention & Logging

**Requirement**: Retain transaction data for compliance, monitoring, and future analytics.

**Details**:
- **Retention**: Minimum 2 years
- **Entry Attempt Data**:
  - Timestamp, store ID, card network
  - Card last 4 (hashed/tokenized only)
  - Entry result (approved/denied/timeout/error)
- **Balance Data**:
  - Available balance returned
  - Required balance (threshold)
  - Threshold multiplier used
  - Pass/fail status
- **Storage**: PCI-compliant data warehouse
- **Access**: SQL queries for ops/product teams

**Priority**: High

---

## Business Requirements

### BR-1: Success Metrics

Measure Phase 1 success via:

1. **Prepaid Entry Approval Rate**
   - % of prepaid customers who meet balance threshold
   - Target: ≥ 60-70% of prepaid customers approved for entry

2. **Payment Completion Rate**
   - % of prepaid customers who approved entry → successful payment at exit
   - Target: ≥ 85% successful completion (BRD mentions 14% nonpayment at Amazon FC baseline)

3. **System Reliability**
   - % uptime of entry gate authorization system
   - Target: No degradation from current JWO performance

4. **Customer Experience**
   - Entry denial message clarity and ease of retry
   - Customer satisfaction with ease of alternative payment method

---

### BR-2: Phase 1 Scope

**In Scope** (Phase 1 MVP):
- ✅ Entry gate balance check via BIN + balance query
- ✅ Threshold-based approval/denial
- ✅ Store-level configuration (threshold, basket size)
- ✅ Comprehensive error handling (timeout, missing balance, missing config)
- ✅ Entry gate display messaging and gate control
- ✅ Preauth reversal  
- ✅ Logging and compliance
- ✅ Real-time dashboard (5-min lag) for ops monitoring
- ✅ US ptech locations only

**Out of Scope** (Phase 2):
- ❌ Real-time balance monitoring during shopping
- ❌ Payment guarantee/backup payment method requirement
- ❌ Partial transaction support (split payments)
- ❌ Multi-processor integration (Phase 2)
- ❌ Global deployment (Phase 2)
- ❌ Mobile app integration (Phase 2)

---

### BR-3: Timeline

**Phase 1 (MVP)**: Target December 31, 2026
- Aligns with BRD deadline
- US ptech only
- Single processor
- Entry gate feature only

**Phase 2 (Enhancement)**: Target Q1/Q2 2027
- Add guarantees, monitoring, multi-processor, global deployment
- Enhanced customer experience features

---

### BR-4: Configuration Defaults

**Default Values** (if not configured per store):
- Threshold multiplier: 3X
- Average basket size: $50
- Implies: Customer needs $150 available balance for entry

**Store-Specific Configuration** (Product Manager Configurable):
- Can adjust threshold multiplier per store (2X, 3X, 4X, etc.)
- Can adjust average basket size per store (based on historical data)
- Changes propagate within 5 minutes

---

## Phase 2 Enhancements (Out of Current Scope)

These features will be added in Phase 2 (post-MVP):

1. **Payment Guarantee Mechanism**
   - Require backup payment method for entry
   - Auto-fallback at checkout if prepaid insufficient

2. **Real-Time Balance Monitoring**
   - Track balance as customer shops
   - Alert customer approaching limit
   - Prevent checkout surprises

3. **Partial Transaction Support**
   - Split payment between prepaid + backup method
   - Charge maximum available from prepaid automatically

4. **Multi-Processor Integration**
   - Support Stripe, Square, Adyen, Shift4
   - Processor routing and fallback logic

5. **Global Deployment**
   - Multi-region infrastructure
   - Data residency per country/region compliance

6. **Mobile App Integration**
   - Real-time app notifications
   - Balance visibility in app
   - Entry/shopping experience integration

---

## Approved Answers Summary (Phase 1 Focused)

| Question | Answer | Phase 1 Implication |
|---|---|---|
| Prepaid Detection | Hybrid (entry + checkout) | Phase 1: entry-only via BIN lookup |
| Preauth Amount | Balance-based | ✅ Phase 1: use actual balance |
| Entry Policy | Guarantee required | Phase 2: add guarantee requirement |
| Insufficient Funds | Partial fulfillment | Phase 2: add auto-fallback |
| Balance Monitoring | Real-time | Phase 2: not in Phase 1 |
| Processors | Multiple | Phase 2: start with single processor |
| Communication | Mobile app | Phase 1: gate display (pivot from app-first) |
| Latency | <100ms | Phase 1: <1-2 seconds (acceptable for gate) |
| Availability | 99.9% | Phase 1: high availability per SLA |
| Geographic | Global | Phase 1: US ptech only |
| Fraud Detection | Basic risk scoring | Phase 2: enhanced fraud detection |
| Compliance | PCI-DSS | ✅ Phase 1: Required |
| Success Metrics | Balanced | ✅ Phase 1: Measured in Phase 1 |
| Timeline | MVP (weeks) | Phase 1: December 31, 2026 |
| Team Capacity | Limited | ✅ Phase 1: Smaller scope fits capacity |
| Infrastructure | Build from scratch | ✅ Phase 1: Greenfield gate service |
| Tech Stack | Cloud-agnostic | ✅ Phase 1: Cloud-agnostic design |
| Integration | Full ecosystem | Phase 1: Entry gate system only |
| Data | Enhanced analytics | ✅ Phase 1: 2-year retention, logging |
| Extensibility | Broader payment | ✅ Phase 1: Designed for Phase 2 |
| Architecture | Recommend best | Phase 1: Simple service layer |
| Build Approach | Hybrid (third-party + custom) | ✅ Phase 1: Use payment processor API |

---

## Next Steps

1. ✅ **Requirements approved** - Phase 1 scope confirmed (BRD-aligned)
2. 🔄 **Proceed to Application Design** - Design entry gate balance check service
3. 🔄 **Units Planning** - Break Phase 1 into development units
4. 🔄 **Construction Phase** - Implement entry gate feature
5. 📅 **Phase 2 Planning** - Post-MVP enhancement roadmap

