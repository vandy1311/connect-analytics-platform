# JWO Prepaid Card Solution - Requirements Specification

**Document Status**: APPROVED FOR CONSTRUCTION  
**Phase**: INCEPTION - Requirements Analysis  
**Date**: 2026-03-16  
**Project**: Just Walk Out (JWO) Prepaid Card Payment Solution  

---

## Executive Summary

This document specifies the requirements for a comprehensive prepaid card payment solution for JWO (Just Walk Out) retail locations. The solution addresses the critical business challenge of payment decline risk for prepaid card customers by implementing:

1. **Hybrid Detection Strategy**: Identify prepaid cards at entry and re-verify at checkout
2. **Balance-Based Preauthorization**: Authorize based on actual card balance rather than fixed amounts
3. **Payment Guarantee Mechanism**: Require customers to provide backup payment method for entry
4. **Real-Time Balance Monitoring**: Track customer spending in real-time with proactive alerts
5. **Graceful Fallback Handling**: Support partial transactions when funds are insufficient
6. **Global Scalability**: Deploy across all JWO locations worldwide with 99.9%+ availability

**Target Timeline**: MVP/Proof of Concept (weeks)  
**Scope**: Multi-location, global rollout  
**Integration**: Full ecosystem integration with existing JWO systems  

---

## Intent Analysis

### Request Summary
Enable prepaid card customers to shop at JWO locations while minimizing payment decline risk through intelligent preauthorization, balance monitoring, and graceful fallback mechanisms.

### Request Type
New Feature - Payment Solution Enhancement

### Scope Estimate
Multiple Components - Involves payment gateway integration, access control, authorization services, customer communication, and analytics

### Complexity Estimate
Complex - Financial transactions, multi-system integration, real-time processing requirements, global compliance mandates

---

## Functional Requirements

### Phase 1 (MVP) — BRD-Aligned Scope

**Note**: Phase 1 focuses on entry gate balance check per the approved BRD. Phase 2 enhancements documented at end of requirements.

### FR-1: Prepaid Card Detection via BIN Lookup

**Requirement**: Identify prepaid cards at entry gate using BIN (Bank Identification Number) database lookup.

**Details**:
- Initiate BIN lookup immediately upon card presentation at entry gate
- Query payment processor for card classification (prepaid vs. credit vs. debit)
- Support Visa, Mastercard, American Express, Discover branded prepaid cards
- Cache BIN lookups for performance (60-second cache acceptable)

**Scope**: Entry Gate System Interface

**Priority**: Critical

**Acceptance Criteria**:
- Card presented at reader → BIN lookup completes <1 second
- Prepaid classification accurate >95% of the time
- Non-network prepaid cards (store gift cards) are not processed

---

### FR-2: Balance-Based Entry Decision (Threshold Check)

**Requirement**: Compare returned prepaid card balance against configurable store threshold to determine entry approval.

**Details**:
- Query available remaining balance from payment processor during preauth
- Retrieve store-level configuration:
  - Threshold multiplier (default: 3X)
  - Average basket size (default: $50)
- Calculate required balance: `threshold_multiplier × average_basket_size`
- **Allow entry IF**: `available_balance ≥ required_balance`
- **Deny entry IF**: `available_balance < required_balance`

**Scope**: Entry Authorization Service

**Priority**: Critical

**Acceptance Criteria**:
- Threshold calculation correct for all configured multipliers
- Configuration changes take effect within 5 minutes
- Latency: <1 second from balance query to approval/denial decision

---

### FR-3: Entry Approval Flow

**Requirement**: Provide clear approval indication and automatic gate opening upon successful balance check.

**Details**:
- Display green approval indicator on entry gate display
- Gate opens automatically within 1-2 seconds of approval
- Log entry with: timestamp, store ID, card network, card last 4 digits (tokenized), approved balance, threshold used
- Do NOT use full card numbers in logs (PCI compliance)

**Scope**: Entry Gate Display, Gate Control System, Logging Service

**Priority**: Critical

---

### FR-4: Entry Denial Flow

**Requirement**: Clearly communicate denial reason and allow customer to retry with different payment method.

**Details**:
- **On Denial**:
  - Gate remains closed
  - Display message: "Insufficient funds available on card. Please use a different payment method."
  - Immediately reverse/void preauth to release customer's funds
- **Retry Options**:
  - Customer can immediately present different card at same reader
  - No cooldown period between attempts
  - Support unlimited retries until successful entry or customer abandonment
- **Logging**: Denial with timestamp, store ID, card last 4 digits (tokenized), available_balance, required_balance

**Scope**: Entry Gate Display, Payment Reversal, Gate Control System, Logging Service

**Priority**: Critical

---

### FR-5: Preauth Reversal (Denial)

**Requirement**: Immediately reverse preauthorization when customer is denied entry.

**Details**:
- Trigger reversal within seconds of entry denial
- Reversal completes before next customer interaction
- Funds returned to customer account per issuer timeline (typically 48 hours)
- Log reversal event for compliance

**Scope**: Payment Gateway Integration

**Priority**: Critical

---

### FR-6: Store Configuration Service

**Requirement**: Allow product managers to configure threshold settings per JWO store location.

**Details**:
- Configure per-store parameters:
  - `threshold_multiplier`: (e.g., 2X, 3X, 4X) - default 3X
  - `average_basket_size`: In dollars - default $50
- Configuration changes take effect within 5 minutes
- If configuration missing, use defaults (do not crash)
- Alert operations team when defaults are used (indicates config admin issue)

**Scope**: Configuration Service, Alerting System

**Priority**: High

**Acceptance Criteria**:
- Configuration UI/API functional and tested
- Default values used gracefully if missing
- Operations alert sent for missing configs

---

## Non-Functional Requirements

### NFR-1: Authorization Latency (Real-Time)

**Requirement**: Preauthorization checks must complete in less than 100ms.

**Details**:
- Entry gate processing: <100ms
- Balance queries: <100ms
- Checkout authorization: <100ms
- Cart update notifications: <500ms acceptable

**Rationale**: Customer experience at entry/exit gates; prevent checkout delays

**Scope**: All real-time APIs

**Priority**: Critical

---

### NFR-2: High Availability (99.9% Uptime)

**Requirement**: System must maintain 99.9%+ availability.

**Details**:
- Target: ≤43 minutes of downtime per month
- Multi-region deployment with failover
- Load balancing across processors
- Graceful degradation (e.g., auto-decline vs. crash)

**Scope**: All services

**Priority**: Critical

---

### NFR-3: Global Scalability

**Requirement**: Support all JWO locations worldwide.

**Details**:
- Horizontal scalability for transaction volume
- Multi-region deployment (Americas, Europe, Asia-Pacific, etc.)
- Latency-optimized for local regions
- Data residency compliance per region

**Scope**: Infrastructure, Database, API Services

**Priority**: High

---

### NFR-4: Basic Fraud Risk Scoring

**Requirement**: Implement basic fraud risk scoring for prepaid card transactions.

**Details**:
- Score transactions on:
  - Unusual transaction amount
  - Location mismatch (if customer location tracked)
  - Frequency of use
  - Balance before vs. after transaction
- Apply rules:
  - Low risk: Approve automatically
  - Medium risk: Flag for review
  - High risk: Require secondary verification or decline
- Rely on payment processor's full fraud suite as secondary layer

**Scope**: Authorization Service, Risk Scoring Engine

**Priority**: Medium

---

### NFR-5: PCI-DSS Compliance

**Requirement**: Maintain full PCI-DSS compliance.

**Details**:
- No storage of full card numbers (tokenization)
- Encrypted transmission of card data
- Secure audit logging
- Access control and role-based permissions
- Regular security assessments
- Compliance with payment processor requirements

**Scope**: All services handling payment data

**Priority**: Critical

---

### NFR-6: Enhanced Data Analytics

**Requirement**: Retain enhanced transaction and customer behavior data.

**Details**:
- Capture transaction data:
  - Customer ID
  - Card type (prepaid/credit/debit - not card number)
  - Transaction amount
  - Prepaid balance before/after
  - Items purchased (SKU, category)
  - Entry/checkout timestamps
  - Location
  - Payment method used (prepaid/guarantee)
- Retention: Minimum 12 months
- Enable analytics for:
  - Prepaid customer behavior
  - Success/failure patterns
  - Fraud trends
  - Operational improvements

**Scope**: Data Collection, Retention, Analytics Export

**Priority**: High

---

## Business Requirements

### BR-1: Success Metrics (Balanced Approach)

**Measurement Areas**:

1. **Payment Decline Reduction**
   - Baseline: Current prepaid card decline rate
   - Target: Reduce by 80%+ through balance-based preauth and guarantee methods
   - Metric: (Declined Transactions / Total Prepaid Transactions) × 100

2. **Prepaid Customer Access Improvement**
   - Baseline: Current % of prepaid customers accessing JWO
   - Target: Increase access by 50%+
   - Metric: (Prepaid Customers Granted Entry / Total Prepaid Customers) × 100

3. **Fraud & Chargeback Reduction**
   - Baseline: Current fraud rate for prepaid transactions
   - Target: Reduce by 60%+ through risk scoring
   - Metric: (Fraud Cases / Total Transactions) × 100

4. **Customer Experience**
   - Target: <2 minute entry process for prepaid customers
   - Target: 95%+ mobile app notification delivery
   - Metric: Customer satisfaction surveys

---

### BR-2: MVP Scope and Timeline

**Phases**:

**Phase 1: MVP (Target: 4-6 weeks)**
- Single payment processor integration (Stripe or Square recommended)
- Basic prepaid detection (BIN-based lookup only)
- Single JWO location pilot
- Mobile app notifications (basic alerts)
- Manual payment guarantee confirmation

**Phase 2: Expansion (4-8 weeks post-MVP)**
- Multi-processor support
- Real-time balance monitoring
- Automatic guarantee method enforcement
- Geographic expansion (5-10 locations)

**Phase 3: Global Rollout (Ongoing)**
- All JWO locations worldwide
- Advanced fraud detection
- Full analytics suite
- Optimization based on learnings

---

### BR-3: Team Constraints

**Constraint**: Limited team capacity for development.

**Mitigation Strategies**:
- Prioritize MVP scope over comprehensive features
- Leverage third-party payment processors (reduce custom payment code)
- Use SaaS solutions where possible
- Archive documentation for knowledge transfer
- Plan for iterative improvements post-MVP

**Recommendation**: Hybrid approach (third-party + custom integration) to balance speed and flexibility

---

### BR-4: Resource & Budget Allocation

**Recommended Hybrid Approach**:

**Third-Party Services (Faster delivery)**:
- Payment processor gateway (Stripe, Square, or similar)
- Fraud detection service (processor-provided)
- Card BIN database and balance lookup service
- Mobile push notification service

**Custom Development (Business-specific)**:
- JWO entry control integration
- Real-time balance monitoring and cart tracking
- Guarantee payment method selection logic
- Partial transaction handling
- Mobile app features
- Analytics and reporting

---

## Technical Requirements

### TR-1: Cloud-Agnostic Architecture

**Requirement**: Design for multi-cloud or cloud-agnostic deployment.

**Details**:
- No vendor lock-in (AWS/Azure/GCP agnostic)
- Container-based services (Docker)
- Infrastructure-as-Code for portability
- REST APIs for service communication

**Scope**: All services

**Priority**: High

---

### TR-2: Build from Scratch

**Requirement**: Establish new payment infrastructure from ground up.

**Details**:
- No legacy systems to integrate with (payment-wise)
- Opportunity to design optimal architecture
- Focus on modularity and extensibility
- Plan for migration to broader payment platform later

**Scope**: Complete infrastructure buildout

**Priority**: Critical

---

### TR-3: Full JWO Ecosystem Integration

**Requirement**: Integrate comprehensively with existing JWO systems.

**Required Integrations**:
- **Entry Control System**: Accept/deny customer entry based on card type and guarantee
- **Cart Management**: Access cart value in real-time
- **Checkout Service**: Process payments with balance + guarantee split
- **Inventory System**: Reduce inventory only for items actually purchased
- **Customer Profile**: Store guarantee payment methods
- **Reporting/Analytics**: Export transaction data

**Integration Method**: REST APIs with event-driven callbacks

**Scope**: Integration layer development

**Priority**: Critical

---

### TR-4: Extensibility for Broader Payment Strategy

**Requirement**: Design as foundation for broader payment strategy.

**Details**:
- Plugin architecture for additional payment methods (future)
- Modular fraud detection (swap implementations)
- Configurable authorization rules
- Event-driven design for webhook-based features
- API versioning for backwards compatibility

**Scope**: Architecture and API design

**Priority**: High

---

## Architecture Recommendations

**Recommended Approach**: Event-Driven Microservices with API Gateway

**Core Services**:

1. **Authorization Service**
   - Preauthorization check at entry
   - Balance-based authorization logic
   - Risk scoring integration
   - Real-time balance queries

2. **Payment Processing Service**
   - Multi-processor routing
   - Transaction settlement
   - Partial payment handling
   - Compliance logging (PCI)

3. **Customer Service**
   - Payment guarantee method management
   - Customer profile data
   - Risk profile tracking

4. **Notification Service**
   - Mobile app push notifications
   - Real-time balance alerts
   - Transaction receipts

5. **Analytics Service**
   - Transaction data ingestion
   - Real-time dashboards
   - Historical reporting
   - Fraud trend analysis

**Integration Pattern**: Event-driven with request/response for authorization phase

**Rationale**: Recommended by AI-DLC based on your answers (architecture agnostic, full ecosystem integration, extensible for future growth)

---

## Success Criteria

**MVP Success**:
- ✅ Prepaid card customers can request entry with guarantee method
- ✅ 80%+ reduction in payment declines for prepaid customers
- ✅ <100ms authorization checks
- ✅ 99.9%+ uptime during pilot
- ✅ PCI-DSS compliance verified
- ✅ Mobile app provides real-time balance visibility

**Phase 2 Success**:
- ✅ Automated guarantee method enforcement
- ✅ Real-time cart tracking with alert system
- ✅ Multi-processor support
- ✅ Expandable to 10+ locations with consistent performance

**Long-term Success**:
- ✅ Global deployment across all JWO locations
- ✅ Foundation for broader payment strategy
- ✅ Positive ROI through fraud/decline reduction
- ✅ Improved prepaid customer segment value

---

## Approved Answers Summary

| Question | Answer | Implication |
|---|---|---|
| Prepaid Detection | Hybrid (entry + checkout) | Two-stage validation |
| Preauthorization Amount | Card balance-based | Accuracy over fixed amounts |
| Entry Policy | Guarantee required | Mitigates risk, allows access |
| Insufficient Funds | Partial fulfillment | Better UX than hard decline |
| Balance Monitoring | Real-time continuous | Proactive customer communication |
| Processors | Multiple | Network flexibility |
| Communication | Mobile app | Modern, real-time notifications |
| Latency SLA | <100ms | High performance required |
| Availability | 99.9% | Enterprise-grade reliability |
| Geographic Scope | Global | Worldwide JWO locations |
| Fraud Detection | Basic risk scoring | Layered security approach |
| Compliance | PCI-DSS | Payment card industry standard |
| Success Metrics | Balanced approach | Multi-dimensional success |
| Timeline | MVP (weeks) | Quick proof of concept |
| Team Capacity | Limited | Hybrid approach recommended |
| Infrastructure | Build from scratch | Greenfield opportunity |
| Tech Stack | Cloud-agnostic | Flexibility, no lock-in |
| Integration Scope | Full ecosystem | Comprehensive solution |
| Data | Enhanced analytics | Deep behavior insights |
| Extensibility | Broader payment strategy | Foundation for growth |
| Architecture | Recommend best approach | Event-driven microservices |
| Build Approach | Hybrid (third-party + custom) | Balance speed and control |

---

## Next Steps

This requirements document is now **APPROVED** and forms the foundation for:

1. **User Stories Phase** (CONDITIONAL) - May be skipped for MVP
2. **Workflow Planning Phase** (NEXT) - Define development workflow and milestones
3. **Application Design Phase** (CONDITIONAL) - May include architecture diagrams
4. **Units Generation Phase** (CONDITIONAL) - Break work into development units
5. **Construction Phase** - Design, code, and test implementation

