# JWO Prepaid Balance Check - Phase 1 Application Design

**Design Document**

**Version**: 1.0  
**Date**: March 16, 2026  
**Project**: JWO Prepaid Card Balance Check - Phase 1 MVP  
**Phase**: Application Design  
**Target Audience**: Architects, Engineers, Technical Leads

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Service Interactions](#service-interactions)
4. [Data Models](#data-models)
5. [API Contracts](#api-contracts)
6. [Error Handling Strategy](#error-handling-strategy)
7. [Non-Functional Requirements Implementation](#non-functional-requirements-implementation)
8. [Deployment Architecture](#deployment-architecture)
9. [Technology Stack](#technology-stack)
10. [Design Patterns](#design-patterns)

---

## Architecture Overview

### System Context

The JWO Prepaid Balance Check system sits at the entry gate of physical JWO locations, intercepting card presentations and determining whether the cardholder has sufficient funds to shop.

**Actors:**
- **Prepaid Cardholder**: Customer at entry gate with prepaid card
- **Gate Hardware**: Card reader, display screen, physical gate controller
- **Payment Processor**: External API for balance queries and reversals
- **Configuration Management**: Per-store settings management
- **Data Warehouse**: Logging and analytics backend
- **Operations Team**: Monitors configurations and system health

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Entry Gate Hardware System                                  │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Card Reader    │  │ Display System   │  │ Gate Control │ │
│  └────────┬───────┘  └────────┬─────────┘  └──────┬───────┘ │
└───────────┼──────────────────┼─────────────────────┼─────────┘
            │                  │                     │
            ▼                  ▼                     ▼
┌──────────────────────────────────────────────────────────────┐
│  Entry Gate Interface (Adapter)                               │
│  - Card data normalization                                   │
│  - Display message routing                                   │
│  - Gate command execution                                    │
└───────────┬──────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────┐
│  Authorization Service (Core Business Logic)                 │
│  - BIN lookup                                                │
│  - Balance query orchestration                               │
│  - Threshold calculation                                     │
│  - Entry decision logic                                      │
└───────┬──────────────────┬───────────────────┬───────────────┘
        │                  │                   │
        ▼                  ▼                   ▼
┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ Payment Processor │  │ Configuration   │  │ Logging &        │
│ Integration      │  │ Service         │  │ Monitoring       │
│                  │  │                 │  │                  │
│ - Preauth        │  │ - Store config  │  │ - Event capture  │
│ - Balance query  │  │ - Defaults      │  │ - Dashboard      │
│ - Reversal       │  │ - Change prop   │  │ - Data warehouse │
└─────────┬────────┘  └────────┬────────┘  └────────┬─────────┘
          │                    │                    │
          ▼                    ▼                    ▼
    [Payment Processor]   [Configuration]    [Data Systems]
                          [Repository]
```

---

## System Components

### 1. Entry Gate Interface

**Responsibility**: Adapt hardware system to internal system interfaces.

**Location**: Edge (entry gate hardware)

**Key Responsibilities:**
- Capture card data from card reader
- Parse card information (BIN, last 4 digits)
- Display approval/denial messages to customer
- Control gate mechanical systems
- Handle physical sensor inputs (gate position, card detection)
- Graceful degradation on communication loss

**Input Interfaces:**
- Card reader events (card swiped, card number)
- Gate sensors (cardholder presence, gate position)

**Output Interfaces:**
- Authorization Service (card data, request ID)
- Gate mechanics (open/close commands)
- Display system (approval/denial/retry messages)

**Internal State:**
- Current request ID
- Gate state (open/closed/opening)
- Last operation timestamp

**Constraints:**
- Minimal processing on edge (push logic to services)
- Must handle offline/degraded scenarios
- <100ms response to card read event

**Dependencies:**
- Payment Processor Integration (via Authorization Service)
- Configuration Service
- Logging Service

---

### 2. Authorization Service (Core)

**Responsibility**: Core business logic for entry authorization decisions.

**Location**: Cloud/On-premises service infrastructure (highly available)

**Key Responsibilities:**

**A. Prepaid Card Detection (FR-1)**
```
CardData → BIN Lookup → Prepaid Classification → {approved, denied_nonsupported}
```

**B. Balance Verification & Threshold Check (FR-2)**
```
CardData + Store_ID → 
  1. Get store config (or defaults)
  2. Initiate preauth with processor
  3. Get balance from response
  4. Calculate required = threshold_multiplier × average_basket_size
  5. Decision: available_balance ≥ required_balance ? APPROVE : DENY
→ {approved, denied_insufficient}
```

**C. Entry Approval (FR-3)**
```
{approved} → 
  1. Log approval event
  2. Trigger gate opening signal
→ GateOpen Event
```

**D. Entry Denial & Preauth Reversal (FR-4, FR-5)**
```
{denied_*} → 
  1. Initiate preauth reversal 
  2. Log denial event
  3. Send denial message to gate display
  4. Allow retry
→ GateClosed Event + ReverseInitiated Event
```

**Input Interfaces:**
- Card Data: `{card_number, card_network, card_last_4}`
- Request ID: `{store_id, timestamp, request_uuid}`
- Configuration: `{threshold_multiplier, average_basket_size}`

**Output Interfaces:**
- Authorization Decision: `{approved/denied, reason, required_balance, available_balance}`
- Event Stream: Entry attempt, approval, denial, reversal events
- Gate Control: Open/Close/Keep-Closed commands

**Key Algorithms:**

**Decision Flow (State Machine):**
```
START
  ▼
┌────────────────────┐
│ Receive Card Data  │
└─────────┬──────────┘
          ▼
┌────────────────────────────┐
│ BIN Lookup (Prepaid Check) │ ──[NOT PREPAID]──▶ DENY + Log
└─────────┬──────────────────┘
          │[PREPAID]
          ▼
┌─────────────────────────────┐
│ Request Preauth Balance     │ ──[TIMEOUT]───────▶ DENY/Timeout + Log
│ from Processor              │  ──[ERROR]────────▶ DENY/Error + Log
└─────────┬────────────────────┘  ──[NO_BALANCE]──▶ DENY/NoBalance + Log
          │[SUCCESS + BALANCE]
          ▼
┌──────────────────────────────┐
│ Get Store Config             │ ──[MISSING]───────▶ Use Defaults + Alert + Log
│ (threshold_mult, avg_basket) │
└─────────┬─────────────────────┘[SUCCESS]
          ▼
┌──────────────────────────────┐
│ Calculate Required Balance   │
│ required = mult × avg_basket │
└─────────┬─────────────────────┘
          ▼
┌──────────────────────────────┐
│ Compare available ≥ required  │
└─────────┬─────────────────────┘
          │
      ┌───┴───┐
      ▼       ▼
    YES      NO
    │        │
    ▼        ▼
  APPROVE   DENY
    │        │
    ▼        ▼
Log + Open  Log + Close + 
            Initiate Reversal
    │        │
    └────┬───┘
         ▼
      END
```

**Latency Budget (NFR-1: <1-2 seconds total):**
- BIN Lookup: <200ms
- Preauth + Balance: <600ms
- Threshold Calc: <50ms
- Decision Logic: <50ms
- Reversal Initiation: <200ms
- Logging: <100ms
- **Total**: ~1100ms (p95)

**Design Patterns:**
- **Circuit Breaker**: Fail to DENY if processor unavailable
- **Timeout**: All processor calls have 800ms timeout
- **Retry Logic**: Transient errors → {retry once, then DENY}
- **Fallback Config**: Use defaults if config unavailable

---

### 3. Configuration Service

**Responsibility**: Manage and propagate per-store threshold settings.

**Location**: Cloud/On-premises service infrastructure

**Key Responsibilities:**
- Store per-location configuration settings
- Provide configuration on-demand to Authorization Service
- Support configuration updates with <5 minute propagation
- Generate alerts when configs are missing
- Support consistent defaults across all locations

**Configuration Model:**
```json
{
  "store_id": "string (unique store identifier)",
  "threshold_multiplier": "number (2.0-10.0x, default: 3.0)",
  "average_basket_size": "number (dollars, default: 50)",
  "enabled": "boolean (true/false, default: true)",
  "created_timestamp": "ISO8601",
  "updated_timestamp": "ISO8601",
  "updated_by": "string (user/system)"
}
```

**Input Interfaces:**
- Configuration requests: `{store_id}`
- Configuration updates: `{store_id, threshold_multiplier?, average_basket_size?, enabled?}`
- Administrative interface for operations team

**Output Interfaces:**
- Configuration response: Full config record
- Change events: Config change stream for <5 min propagation
- Alert events: Missing config alerts

**Propagation Mechanism:**
- **Immediate Response**: Direct API calls get live config
- **Push Updates**: Event stream notifies consumers of changes  
- **Cache Strategy**: Edge nodes cache with <5 min TTL
- **Fallback**: In-memory defaults if service unavailable

**Default Values:**
```json
{
  "threshold_multiplier": 3.0,
  "average_basket_size": 50,
  "enabled": true
}
```

---

### 4. Payment Processor Integration

**Responsibility**: Encapsulate payment processor API interactions.

**Location**: Service layer (cloud/on-premises)

**Key Responsibilities:**
- Abstract payment processor API details
- Request preauth with balance return
- Handle error responses gracefully
- Initiate reversal/void on denials
- Ensure PCI-DSS compliance (tokenize sensitive data)
- Implement timeout policies
- Support future multi-processor expansion

**Supported Processors (Phase 1):** Single processor (TBD: Visa, Mastercard, processor choice)

**API Abstraction Layer:**

**Method: QueryBalance(request)**
```
Input:
  - card_number (will be tokenized)
  - card_network (Visa/MC/Amex/Discover)
  - amount (preauth amount = required_balance)
  - store_id
  - request_id (unique identifier)

Output:
  {
    "status": "approved|declined|error|timeout",
    "available_balance": decimal,
    "preauth_id": string,
    "error_code": string,
    "error_message": string,
    "response_time_ms": integer
  }

SLA:
  - p95 response time: <600ms
  - All responses: <1000ms
  - Timeouts: 800ms
```

**Method: ReversePreauth(preauth_id)**
```
Input:
  - preauth_id (from QueryBalance response)
  - request_id (unique identifier)
  - store_id

Output:
  {
    "status": "voided|error|timeout",
    "voided_amount": decimal,
    "error_code": string,
    "error_message": string,
    "response_time_ms": integer
  }

SLA:
  - p95 response time: <200ms
  - Initiated within: <100ms of denial decision
```

**Security Implementation (PCI-DSS):**
- **Tokenization**: Never store full card number in logs
  - On input: Tokenize; use token for processing
  - In logs: Store last 4 + token only
  - Output: Never return full card number
- **Encryption**: All API calls over TLS 1.2+
- **Access Control**: Limited to Authorization Service
- **Audit Logging**: All processor interactions logged immutably

**Error Handling:**
```
Processor Response → Action:
  approved w/ balance   → Return balance
  declined              → Return error (card declined)
  error response        → Return error (processor error)
  timeout (>800ms)      → Return timeout error
  network unavailable   → Return unavailable error
```

---

### 5. Logging & Monitoring Service

**Responsibility**: Capture events, enable analytics, support compliance.

**Location**: Cloud/On-premises data warehouse

**Key Responsibilities:**
- Capture authorization events (attempt, approval, denial, error)
- Store 2-year event history
- Enable real-time dashboard (5-minute lag)
- Support SQL queries for analytics
- Ensure PCI-DSS compliance (tokenization, encryption)
- Generate operational alerts

**Event Schema:**

**Entry Attempt Event**
```json
{
  "event_id": "uuid",
  "event_type": "entry_attempt",
  "timestamp": "ISO8601 (UTC)",
  "store_id": "string",
  "card_network": "enum (Visa, Mastercard, Amex, Discover)",
  "card_last_4_hashed": "SHA256(card_last_4)",
  "card_token": "processor-token (not full number)",
  "available_balance_cents": "integer",
  "required_balance_cents": "integer",
  "threshold_multiplier_used": "float",
  "decision": "approved|denied|denied_timeout|denied_no_balance|denied_nosupport|denied_missing_config",
  "processor_response_time_ms": "integer",
  "total_decision_time_ms": "integer",
  "request_id": "uuid"
}
```

**Approval Event**
```json
{
  "event_id": "uuid",
  "event_type": "approval",
  "timestamp": "ISO8601",
  "store_id": "string",
  "card_last_4_hashed": "SHA256(card_last_4)",
  "available_balance_cents": "integer",
  "threshold_multiplier_used": "float",
  "gate_open_timestamp": "ISO8601",
  "request_id": "uuid"
}
```

**Denial Event**
```json
{
  "event_id": "uuid",
  "event_type": "denial",
  "timestamp": "ISO8601",
  "store_id": "string",
  "denial_reason": "insufficient_funds|timeout|no_balance|not_prepaid|missing_config",
  "card_last_4_hashed": "SHA256(card_last_4)",
  "available_balance_cents": "integer",
  "required_balance_cents": "integer",
  "request_id": "uuid"
}
```

**Reversal Event**
```json
{
  "event_id": "uuid",
  "event_type": "reversal",
  "timestamp": "ISO8601",
  "preauth_id": "string",
  "reversal_status": "initiated|voided|failed",
  "reversal_timestamp": "ISO8601",
  "request_id": "uuid"
}
```

**Error Event**
```json
{
  "event_id": "uuid",
  "event_type": "error",
  "timestamp": "ISO8601",
  "store_id": "string",
  "error_type": "processor_timeout|processor_error|config_missing|internal_error",
  "error_message": "string",
  "severity": "warning|error|critical",
  "request_id": "uuid"
}
```

**Storage:**
- **Format**: JSON events in data warehouse
- **Retention**: 2 years minimum (730 days)
- **Partitioning**: By date (YYYY-MM-DD) for efficient queries
- **Access Control**: Role-based (Finance, Product, Ops teams)
- **Compliance**: PCI-DSS audit logging (immutable, access logged)

**Real-Time Dashboard Metrics (5-min lag):**
```
Overall Metrics:
  - Total transactions (last 24h, last 7d, last month)
  - Approval rate (%)
  - Denial breakdown (insufficient, timeout, nosupport, etc.)
  - Average available balance
  - Average required balance
  - Average decision time (p50, p95, p99)
  - System errors (count, severity distribution)

Per-Store Metrics:
  - Store transaction count
  - Store approval rate
  - Store average balance (available/required)
  - Store error rate

Operational Alerts:
  - Missing config alert (no config for store_id)
  - High error rate (>5% errors)
  - High timeout rate (>10% timeouts)
  - Slow decision time (p95 > 1.5s)
  - Processor unavailability
  - System health alerts
```

---

## Service Interactions

### Main Entry Flow (Happy Path)

**Sequence: Prepaid Customer with Sufficient Funds**

```
Cardholder                  Gate Interface          Authorization Service
    │                            │                         │
    ├─ Presents card ────────────┤                         │
    │                            │                         │
    │                      [Parse card data]                │
    │                            │                         │
    │                      [Send to Auth Service]          │
    │                            ├────────────────────────┤
    │                            │    CardData Request    │
    │                            │                        │
    │                      [Wait for decision]     1. BIN lookup
    │                            │                2. Get config
    │                            │                3. Preauth + balance
    │                            │                4. Threshold check
    │                            │                5. Approve decision
    │                            │◄────────────────────────┤
    │                            │   Approved Decision    │
    │                            │ {balance: $175, req: $150}
    │                            │                        │
    │                      [Display approval]   [Log approval event]
    │                            │
    │◄─ Green indicator + ───────┤
    │   Gate opens               │
    │                       [Send gate open cmd]
    │                            │
    ▼                            ▼
  [Enters store]          [Gate opens 1-2s]
```

**Timing:**
- Card read to decision: ~1-2 seconds
- Decision display: <200ms
- Gate opening: <1-2 seconds total

---

### Entry Denial Flow (Insufficient Funds)

**Sequence: Prepaid Card with Insufficient Balance**

```
Cardholder                  Gate Interface          Authorization Service
    │                            │                         │
    ├─ Presents prepaid card ────┤                         │
    │(insufficient balance)       │                         │
    │                            │                         │
    │                      [Parse card data]                │
    │                            ├────────────────────────┤
    │                            │ CardData: avail $125  │
    │                      [Wait for decision]    1. BIN lookup ✓
    │                            │                2. Get config ✓
    │                            │                3. Preauth + balance ✓
    │                            │                4. Calculate: 3x$50 = $150 required
    │                            │                5. DENY: $125 < $150
    │                            │◄────────────────────────┤
    │                            │   DENIED Decision      │
    │                            │ {available: $125, required: $150}
    │                            │                        │
    │                      [Display denial msg]  [Initiate reversal]
    │                            │ "Insufficient funds..." [Log denial event]
    │                      [Close gate]
    │                            │
    │◄─ Red indicator + ─────────┤
    │   Gate closed              │
    │                            │
    ├─ [Can retry with different card]
    │                            │
    ├─ Presents VISA debit card ─┤ [Process continues from BIN lookup]
    │(has $200 available)        │
    │                            │
    │                      [Parse card data]                │
    │                            ├────────────────────────┤
    │                            │ CardData: avail $200  │
    │                            │                        │
    │                            │ DEBIT CARD (not prepaid)
    │                            │ → DENY, not supported
    │                            │◄────────────────────────┤
    │                            │ DENIED (not prepaid)   │
    │                      [Display error msg]
    │                            │ "Please use prepaid..."│
    │                            │
    │├─ [Can retry again]        │
    │                            │
    ├─ Presents different card ──┤ [Process continues]
    │                            ▼
```

---

### Timeout & Error Handling Flow

**Sequence: Processor Timeout or Missing Balance**

```
Cardholder                  Gate Interface          Authorization Service
    │                            │                         │
    ├─ Presents card ────────────┤                         │
    │                            ├────────────────────────┤
    │                            │ CardData Request       │
    │                            │                        │
    │                      [Wait for decision] 1. BIN lookup ✓
    │                            │                2. Get config ✓
    │                            │                3. Call processor...
    │                            │                   [timeout after 800ms]
    │                            │                4. DENY (timeout)
    │                            │
    │                            │◄────────────────────────┤
    │                            │ DENIED (timeout)       │
    │                            │                        │
    │                      [Display msg]       [LOG ERROR]
    │                            │ "Authorization timeout"│
    │                      [Close gate]        [ALERT TEAM]
    │                            │                        │
    │◄─ Yellow indicator + ──────┤                        │
    │   Gate stays closed        │                        │
    │                            │                        │
    ├─ [Can retry immediately]   │                        │
    │                            │                        │
    ▼                            ▼                        ▼
```

---

### Configuration Missing Flow

**Sequence: First Entry at New Store (Config Missing)**

```
Cardholder                  Gate Interface          Authorization Service     Config Service
    │                            │                         │                      │
    ├─ Presents card ────────────┤                         │                      │
    │ (new store, no config)     │                         │                      │
    │                            ├────────────────────────┤                       │
    │                            │ CardData + Store123    │                       │
    │                            │                        │                       │
    │                      [Wait for decision] 1. BIN lookup ✓              
    │                            │                2. Request config for store123  │
    │                            │                 ├──────────────────────────────┤
    │                            │                 │ NO CONFIG FOUND              │
    │                            │                 ◄──────────────────────────────┤
    │                            │                 3. Use defaults (3x, $50) ✓
    │                            │                4. Preauth + balance ✓
    │                            │                5. Threshold: 3 × $50 = $150
    │                            │                6. Approve/Deny based on balance
    │                            │                7. [ALERT: Missing config for store123]
    │                            │◄────────────────────────┤
    │                            │ APPROVED/DENIED        │
    │                            │ (with defaults)        │
    │                            │                        │
    │                            │                        │ [Ops team receives alert]
    │                            │                        │ "Configure store123 settings"
    │                      [Gate opens/closes]   [LOG: Missing config used]
    │                            │                        │
    │                      [Display approval/denial]      │
    │                            │                        │
    ▼                            ▼                        ▼
```

---

## Data Models

### Core Entities

**Card Data (Input)**
```
CardData:
  card_number: string (will be tokenized)
  card_last_4: string (4 digits)
  card_network: enum (Visa, Mastercard, Amex, Discover)
  card_type: enum (prepaid, debit, credit, unknown)
  cardholder_name: string (may be unavailable)
  expiration_date: string (MM/YYYY)
```

**Entry Request**
```
EntryRequest:
  request_id: UUID (unique identifier)
  store_id: string (location identifier)
  timestamp: ISO8601 (request timestamp, UTC)
  card_data: CardData
  processor_request_id: UUID (sent to processor)
```

**Authorization Decision**
```
AuthorizationDecision:
  request_id: UUID
  decision: enum (approved, denied_insufficient, denied_timeout, denied_no_balance, 
                  denied_not_prepaid, denied_missing_config)
  reason: string (human-readable reason)
  available_balance_cents: integer (in cents, int to avoid float errors)
  required_balance_cents: integer (calculated: multiplier × average_basket)
  threshold_multiplier_used: float
  decision_timestamp: ISO8601
  processor_response_time_ms: integer
  total_decision_time_ms: integer
```

**Store Configuration**
```
StoreConfig:
  store_id: string (unique, immutable)
  threshold_multiplier: float (2.0-10.0, default 3.0)
  average_basket_size_cents: integer (dollars×100, default 5000)
  enabled: boolean (default true)
  created_timestamp: ISO8601
  updated_timestamp: ISO8601
  updated_by: string (user/system identifier)
  notes: string (optional)
```

**Event (for logging)**
```
Event:
  event_id: UUID (unique)
  event_type: enum (entry_attempt, approval, denial, reversal, error, config_change, alert)
  timestamp: ISO8601 (UTC)
  store_id: string
  request_id: UUID
  data: JSON (event-specific payload)
  severity: enum (info, warning, error, critical)
```

---

## API Contracts

### Authorization Service API

**Endpoint: POST /authorize/check-entry**

**Request:**
```json
{
  "store_id": "string (e.g., 'store-123')",
  "card_data": {
    "card_number": "string",
    "card_network": "enum (visa|mastercard|amex|discover)",
    "card_last_4": "string (4 digits)"
  },
  "request_id": "uuid",
  "timestamp": "ISO8601"
}
```

**Response (Approved):**
```json
{
  "decision": "approved",
  "request_id": "uuid",
  "available_balance_cents": 17500,
  "required_balance_cents": 15000,
  "threshold_multiplier_used": 3.0,
  "decision_timestamp": "ISO8601",
  "processor_response_time_ms": 450,
  "total_decision_time_ms": 520
}
```

**Response (Denied - Insufficient):**
```json
{
  "decision": "denied_insufficient",
  "reason": "Available balance $125 is less than required $150",
  "request_id": "uuid",
  "available_balance_cents": 12500,
  "required_balance_cents": 15000,
  "decision_timestamp": "ISO8601",
  "processor_response_time_ms": 600,
  "total_decision_time_ms": 650
}
```

**Response (Denied - Timeout):**
```json
{
  "decision": "denied_timeout",
  "reason": "Authorization request timed out after 800ms",
  "request_id": "uuid",
  "decision_timestamp": "ISO8601",
  "processor_response_time_ms": 800,
  "total_decision_time_ms": 820
}
```

**HTTP Status Codes:**
- `200`: Decision made (check decision field)
- `400`: Bad request (invalid input)
- `408`: Request timeout
- `500`: Internal server error
- `503`: Service unavailable

---

### Configuration Service API

**Endpoint: GET /config/store/{store_id}**

**Response:**
```json
{
  "store_id": "string",
  "threshold_multiplier": 3.0,
  "average_basket_size_cents": 5000,
  "enabled": true,
  "created_timestamp": "ISO8601",
  "updated_timestamp": "ISO8601",
  "updated_by": "system"
}
```

**Endpoint: POST /config/store/{store_id}**

**Request:**
```json
{
  "threshold_multiplier": 3.5,
  "average_basket_size_cents": 6000,
  "notes": "Updated for Q2 campaign"
}
```

**Response:**
```json
{
  "store_id": "string",
  "threshold_multiplier": 3.5,
  "average_basket_size_cents": 6000,
  "enabled": true,
  "created_timestamp": "ISO8601",
  "updated_timestamp": "ISO8601 (NEW)",
  "updated_by": "user@company.com"
}
```

**HTTP Status Codes:**
- `200`: Success
- `404`: Store not found
- `400`: Bad request
- `409`: Conflict (concurrent update)
- `500`: Internal error

---

### Logging Service API

**Endpoint: POST /events/log**

**Request:**
```json
{
  "event_id": "uuid",
  "event_type": "entry_attempt",
  "timestamp": "ISO8601",
  "store_id": "string",
  "request_id": "uuid",
  "data": {
    "decision": "approved",
    "available_balance_cents": 17500,
    "required_balance_cents": 15000
  }
}
```

**Response:**
```json
{
  "event_id": "uuid",
  "status": "logged",
  "timestamp": "ISO8601"
}
```

---

## Error Handling Strategy

### Error Classification

**Processor Errors (External):**
```
Scenario: Processor timeout > 800ms
- Handle: Abort with DENY_TIMEOUT decision
- Action: Close gate, display retry message
- Log: ERROR severity, timeout event
- Alert: If >10% timeouts in 5 min window

Scenario: Processor returns error code
- Handle: Abort with DENY_ERROR decision
- Action: Close gate, display generic error message
- Log: ERROR severity with error code
- Alert: If >5% errors in 5 min window

Scenario: Processor returns no balance field
- Handle: Abort with DENY_NO_BALANCE decision (fail-safe)
- Action: Close gate, display "Unable to verify balance" message
- Log: WARNING severity
- Alert: If >1% on same processor, escalate
```

**Configuration Errors (Internal):**
```
Scenario: Store config missing
- Handle: Use defaults (3.0x multiplier, $50 basket)
- Action: Process entry with defaults, continue
- Log: INFO severity, "config missing, used defaults"
- Alert: ALERT to ops team "Configure store {store_id}"
- Timeout: <5 minutes to config update

Scenario: Config corrupted/invalid
- Handle: Use defaults, log error
- Action: Use defaults, escalate to ops
- Log: ERROR severity
- Alert: ALERT to ops team
```

**Network Errors (Infrastructure):**
```
Scenario: Cannot reach payment processor
- Handle: Circuit breaker - DENY entry
- Action: Close gate, "Authorization unavailable" message
- Log: ERROR severity
- Alert: CRITICAL alert to ops
- Recovery: Auto-retry within Circuit Breaker window

Scenario: Cannot reach config service
- Handle: Use cached config or defaults
- Action: Continue with cache/defaults
- Log: WARNING severity
- Alert: None (automatic fallback)

Scenario: Cannot reach logging service
- Handle: Continue (logging is not critical path)
- Action: Queue events locally, retry async
- Log: WARNING in local log
- Alert: INFO alert to team
```

**Card Data Errors (Input):**
```
Scenario: Invalid/unrecognized card network
- Handle: DENY_NOT_PREPAID
- Action: Close gate, "Please use prepaid card" message
- Log: INFO severity
- Alert: None

Scenario: Card number format invalid
- Handle: DENY entry with bad_request reason
- Action: Close gate, "Card read error, please retry"
- Log: INFO severity
- Alert: None (expected input error)
```

---

## Non-Functional Requirements Implementation

### NFR-1: Authorization Latency (<1-2 seconds)

**Requirement:** Total time from card presentation to gate movement <1.5 seconds (p95)

**Implementation:**

| Component | Target | Strategy |
|-----------|--------|----------|
| Card read | <100ms | Edge optimization (minimal processing) |
| Data transmission | <100ms | Local network optimization |
| BIN lookup | <200ms | In-memory cache or fast service |
| Config retrieval | <100ms | Distributed cache with TTL |
| Preauth request | <600ms | Processor SLA + timeout policy |
| Balance extraction | <50ms | In-memory operation |
| Threshold calc | <50ms | In-memory arithmetic |
| Reversal (if needed) | <200ms | Background/async when possible |
| Gate opening | <1-2s | Hardware constraint (acceptable) |
| **Total** | **<1500ms** | Parallel processing where possible |

**Optimization Strategies:**
1. **Caching**: BIN database cached locally
2. **Parallelization**: Fetch config and initiate preauth in parallel
3. **Async Operations**: Logging and reversal async to critical path
4. **Early Termination**: BIN lookup fails fast (not prepaid)
5. **Processor SLA**: Enforce <600ms timeout
6. **Local Processing**: Minimize remote calls

**Monitoring:**
- Track decision time p50, p95, p99 per store
- Alert if p95 exceeds 1.5 seconds sustained
- Dashboard metric: "Entry Decision Latency"

---

### NFR-2: Availability & Reliability (Circuit Breaker Pattern)

**Requirement:** Maintain gate operation availability; fail-safe on processor unavailability

**Implementation:**

**Circuit Breaker State Machine:**
```
                ┌─────────┐
                │ CLOSED  │ (Normal operation)
                │ (accept)│ Processor working
                └────┬────┘
                     │ (Error Rate > 50% in 1min)
                     ▼
        ┌────────────────────┐
        │   OPEN             │ (Failing requests)
        │ (fail-safe DENY)   │ Stop calling processor
        └────┬────────────────┘
             │ (After 2 minutes)
             ▼
        ┌────────────────────┐
        │ HALF-OPEN          │ (Test recovery)
        │ (allow 1 request)  │ Try calling processor
        └──┬────────────┬────┘
           │ Success    │ Failure
           │            │
        ┌──▼─┐      ┌───▼──┐
        │CLOSED    │OPEN  │
        └────┘     └──────┘
```

**Behavior:**
- **CLOSED**: Process normally, collect metrics
- **OPEN**: DENY all entries with "unavailable" reason, daily alert
- **HALF-OPEN**: Allow single test request to processor
  - Success → CLOSED
  - Failure → OPEN

**Monitoring:**
- Track processor call success rate
- Track circuit breaker state changes
- Alert on state transitions to OPEN
- Log all state changes

---

### NFR-3: PCI-DSS Compliance

**Requirement:** Full PCI-DSS compliance for cardholder data

**Implementation:**

| Requirement | Implementation |
|-------------|-----------------|
| No storage of full card | Tokenize on input; use token only |
| Encrypted transmission | TLS 1.2+ for all processor calls |
| Access controls | Service-to-service auth (mTLS) |
| Card masking in logs | Log only: `last_4_hashed`, token |
| Audit logging | Immutable event store, 7-year retention |
| Data deletion | Processor handles retention per PCI |

**Card Data Flow:**
```
Input: card_number (from gate hardware)
  ▼
[Tokenize with processor] → Get token
  ▼
Internal: token + card_last_4_hashed (SHA256)
  ▼
Logging: event with {token, card_last_4_hashed}
  ▼
Query: Can query by token, never by full number
  ▼
Output: Never return card_number in any API response
```

**Audit Logging (Immutable):**
- Every processor API call logged
- Every authorization decision logged
- Every config change logged
- Log access tracked (who accessed what, when)
- 7-year retention (PCI requirement)

---

### NFR-4: Geographic Scope (US Ptech)

**Requirement:** Phase 1 limited to US ptech locations

**Implementation:**
- Configuration validates store_id against US ptech list
- Non-US stores: Config blocked, DENY entry with "not available" message
- Data warehouse: US regional hosting
- Processor: US endpoint only
- Phase 2: Expand to global endpoints

---

### NFR-5: Data Retention & Logging (2-year min)

**Requirement:** 2-year event retention for analytics/compliance

**Implementation:**
- Event store: Data warehouse with 730-day retention
- Partitioning: By date (YYYY-MM-DD) for efficient queries
- Archive: Nightly to long-term storage after 2 years (optional, depends on legal)
- Access: SQL-queryable via analytics tools
- Compliance: PCI-DSS audit logging (immutable)

**Retention Policy:**
```
Day 0: Event created
Days 1-30: Hot storage (fast queries, real-time dashboard)
Days 31-365: Warm storage (slower queries, analytics)
Days 366-730: Cold storage (archive, rare queries)
Day 731+: Delete (or move to legal hold)
```

---

## Deployment Architecture

### Service Deployment

**Phase 1 Deployment Topology:**

```
┌─────────────────────────────────────┐
│  Entry Gate Hardware Layer          │
│  (At physical JWO location)         │
│  ┌────────────────┐                 │
│  │ Entry Gate     │                 │
│  │ Interface      │ (Edge compute)  │
│  │ - Card reader  │ <5 minutes      │
│  │ - Display      │ offline         │
│  │ - Gate ctrl    │ resilient       │
│  └────────┬───────┘                 │
└───────────┼──────────────────────────┘
            │ (HTTPS, encrypted)
            ▼
┌─────────────────────────────────────┐
│  Cloud/On-Premises Service Layer    │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ Authorization Service (HA)    │  │
│  │ - Stateless                   │  │
│  │ - Replicated across zones    │  │
│  │ - Load balanced               │  │
│  └────┬──────────┬──────────┬───┘   │
│       │          │          │       │
│  ┌────▼──┐ ┌─────▼──┐ ┌────▼──┐   │
│  │Config │ │Logging │ │Payment│   │
│  │Service│ │Service │ │Integ  │   │
│  │(cache)│ │(queue) │ │(mTLS) │   │
│  └───────┘ └────────┘ └───────┘   │
└─────────┬──────────┬───────┬───────┘
          │          │       │
          ▼          ▼       ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Config      │ │Data      │ │ Payment      │
│  Repository  │ │Warehouse │ │ Processor    │
│  (Database)  │ │(BigQuery)│ │ (External)   │
└──────────────┘ └──────────┘ └──────────────┘
```

**Architectural Principles:**
- **Stateless Services**: Easy scaling, no affinity issues
- **High Availability**: Multi-zone deployment, no SPOF
- **Resilience**: Circuit breaker, timeout policies, fallbacks
- **Observability**: Centralized logging, metrics, tracing
- **Security**: Service-to-service auth (mTLS), encryption, secrets management

---

## Technology Stack

### Recommended Stack (Cloud-Agnostic)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Java/Go/Python | Mature, strong ecosystem, excellent libraries |
| **Framework** | Spring Boot/Gin/FastAPI | Standard frameworks, web framework agnostic |
| **Database** | PostgreSQL | Relational, ACID, handles config well |
| **Caching** | Redis | In-memory caching for BIN/config, high throughput |
| **Message Queue** | Kafka/RabbitMQ | Event streaming, config propagation |
| **Data Warehouse** | BigQuery/Snowflake/Athena | SQL-queryable, petabyte-scale, cost-effective |
| **Monitoring** | Prometheus/Datadog | Metrics, alerting, dashboards |
| **Logging** | ELK/Cloudwatch | Centralized logs, searchable |
| **Authentication** | mTLS + OAuth2 | Service-to-service auth, human auth |
| **Container** | Docker | Deployment packaging |
| **Orchestration** | Kubernetes | Scaling, self-healing, upgrades |

### BIN Lookup Service

**Phase 1 Approach:**
- **Option 1**: Pre-load BIN database into Redis at startup
  - Trade-off: Fast (<50ms), requires memory, updates require restart
- **Option 2**: Call BIN lookup service (external)
  - Trade-off: Network latency (~100-200ms), no local state, easier updates
- **Option 3**: Hybrid: Cache top 500 BINs locally, fallback to service
  - Trade-off: Balanced approach, moderate complexity

**Recommendation:** Option 1 (Redis cache locally) for Phase 1 MVP
- BIN database is ~100K entries (small), fits in memory
- Reload daily for updates
- Extremely fast lookups

---

## Design Patterns

### 1. Circuit Breaker

Used for processor unavailability resilience.

**States:**
- **CLOSED**: Normal, forward requests
- **OPEN**: Error rate exceeded, fail-fast
- **HALF-OPEN**: Test recovery, allow single request

**Configuration:**
- Error threshold: 50% failures in 1 minute
- Timeout to half-open: 2 minutes
- Success threshold (half-open): 1 success → closed

---

### 2. Timeout Policy

All processor calls must timeout.

**Configuration:**
- Preauth timeout: 800ms
- Reversal timeout: 600ms
- Config fetch: 500ms timeout, fallback to cache

**Implementation:**
```
Pseudocode:
try {
  result = callProcessor(...)
    .withTimeout(800, MILLISECONDS)
} catch (TimeoutException) {
  return DENY_TIMEOUT_DECISION
}
```

---

### 3. Graceful Degradation

Continue with defaults when services unavailable.

**Hierarchy:**
1. Get live config from service
2. If service unavailable, use cached config
3. If no cache, use hardcoded defaults
4. Log degradation event, alert ops

---

### 4. Async Logging

Critical path: Authorization decision
Non-critical: Logging (handle async)

**Pattern:**
```
sync: Make decision → return to gate
async: Log event → data warehouse
```

---

### 5. Idempotency

All operations must be idempotent (safe to retry).

**Request ID Usage:**
- Every request gets unique UUID
- Log includes request_id
- Processor calls include request_id for deduplication
- Retry with same request_id = same result

---

## Summary

**Phase 1 Architecture Principles:**
1. **Simplicity**: Single processor, single decision (approve/deny), minimal state
2. **Resilience**: Circuit breaker, timeouts, fallbacks, fail-safe defaults
3. **Compliance**: PCI-DSS by design, tokenization, encryption, audit logging
4. **Observability**: Comprehensive logging, real-time metrics, alerting
5. **Scalability**: Stateless services, caching, async logging
6. **Reliability**: <1.5s latency, >99% availability, clear error handling

**Next Phase: Units Planning**
- Break architecture into development units
- Define unit boundaries and dependencies
- Estimate effort per unit
- Schedule implementation sprints

---

**Document Version**: 1.0  
**Last Updated**: March 16, 2026  
**Status**: Design Complete  
**Next Phase**: Units Planning  
**Approved By**: [Product Lead] (pending)
