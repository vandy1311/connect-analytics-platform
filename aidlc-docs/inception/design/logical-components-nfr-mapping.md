# Logical Components & Non-Functional Requirements Mapping

**Document**: Logical Component to NFR Traceability  
**Version**: 1.0  
**Date**: March 16, 2026  
**Purpose**: Map Phase 1 logical components to non-functional requirements

---

## Table of Contents

1. [Logical Components Overview](#logical-components-overview)
2. [Logical Component Definitions](#logical-component-definitions)
3. [NFR to Component Traceability Matrix](#nfr-to-component-traceability-matrix)
4. [Component-Level NFR Implementations](#component-level-nfr-implementations)

---

## Logical Components Overview

### System Decomposition

The JWO Prepaid Balance Check system is logically decomposed into **7 core logical components** organized into 3 tiers:

**Tier 1: Edge/Presentation**
- Entry Gate Interface (card reader, display, gate controls)

**Tier 2: Application/Business Logic**
- Authorization Service (decision engine)
- Configuration Service (threshold settings)
- Logging & Event Service (audit trail)

**Tier 3: Integration/Support**
- Payment Processor Integration (balance queries)
- Health & Monitoring (system observability)
- Data Warehouse Integration (analytics)

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: Edge/Presentation                                   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Entry Gate Interface                                  │   │
│ │ • Card reader adapter                                │   │
│ │ • Display message router                             │   │
│ │ • Gate controller                                    │   │
│ └───────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│ Tier 2: Application/Business Logic                          │
│ ┌──────────────────────┐ ┌─────────────────────────────┐    │
│ │ Authorization        │ │ Configuration Service       │    │
│ │ Service              │ │ • Store config management   │    │
│ │ • BIN lookup         │ │ • Default values            │    │
│ │ • Preauth query      │ │ • Change propagation        │    │
│ │ • Balance logic      │ │ • Distributed cache         │    │
│ │ • Decision engine    │ │ • Missing config alerts     │    │
│ └────────┬─────────────┘ └──────────────┬──────────────┘    │
│          │                              │                   │
│ ┌────────┴──────────────────────────────┴──────────────┐    │
│ │ Logging & Event Service                            │    │
│ │ • Authorization event capture                       │    │
│ │ • PCI-DSS compliant masking                         │    │
│ │ • Event queue publishing                            │    │
│ │ • Audit trail maintenance                           │    │
│ └───────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────┐
│ Tier 3: Integration/Support                                 │
│ ┌──────────────────────┐ ┌─────────────────────────────┐    │
│ │ Payment Processor    │ │ Health & Monitoring         │    │
│ │ Integration          │ │ • Circuit breaker           │    │
│ │ • BIN lookup API     │ │ • Metrics collection        │    │
│ │ • Preauth API        │ │ • Health check endpoints    │    │
│ │ • Preauth reverse    │ │ • Latency tracking          │    │
│ │ • Timeout handling   │ │ • Error rate monitoring     │    │
│ │ • Retry logic        │ │ • State tracking            │    │
│ └──────────────────────┘ │ • Alert triggering          │    │
│                          └──────────────┬───────────────┘    │
│                                         │                    │
│ ┌────────────────────────────────────┬──┴──────┐             │
│ │ Data Warehouse Integration         │         │             │
│ │ • Event stream consumption         │ (Cloud/ │             │
│ │ • Data transformation              │  hosted)│             │
│ │ • Warehouse ingestion              │         │             │
│ │ • Retention policy enforcement     │         │             │
│ └────────────────────────────────────┴──────────┘            │
└───────────────────────────────────────────────────────────────┘
```

---

## Logical Component Definitions

### 1. Entry Gate Interface (Tier 1)

**Purpose**: Adapt physical hardware to system APIs

**Boundaries**:
- **Upstream**: Hardware (card reader, display, gate motors)
- **Downstream**: REST API to Authorization Service

**Key Responsibilities**:
- Parse card data from card reader
- Normalize card information
- Send authorization requests
- Route display messages to hardware
- Execute gate control (open, close, keep-closed)
- Handle offline scenarios (degraded operation)

**Inputs**:
- Card reader events: `{card_number, card_network, card_last_4}`
- Gate sensors: `{cardholder_present, gate_position}`

**Outputs**:
- Authorization requests: `{store_id, card_data, request_id}`
- Display messages: `{text, color, duration_ms}`
- Gate commands: `{OPEN, CLOSE, KEEP_CLOSED}`

**NFR Concerns**:
- **Latency (NFR-1)**: <100ms response to card read
- **Availability (NFR-2)**: Offline operation, local fallback
- **Reliability**: Sensor error handling

**Key Constraints**:
- Minimal processing (push logic to services)
- Must handle network loss
- <100ms response to card event
- Atomic operations (card read → decision → gate action)

---

### 2. Authorization Service (Tier 2 - Core)

**Purpose**: Make entry authorization decisions based on card and account data

**Boundaries**:
- **Upstream**: Entry Gate Interface (card data)
- **Downstream**: Payment Processor, Configuration Service, Logging Service

**Key Responsibilities**:
- Perform BIN lookup for card type classification
- Query processor for cardholder balance
- Retrieve store configuration (threshold, basket size)
- Calculate required balance threshold
- Compare available vs required balance
- Make approve/deny decision
- Initiate preauth reversal on denial

**Inputs**:
- Card data: `{card_number, card_network, card_last_4}`
- Store ID: Unique store identifier
- Request ID: Unique request transaction ID

**Outputs**:
- Authorization decision: `{APPROVED, DENIED_NOT_PREPAID, DENIED_INSUFFICIENT, ...}`
- Event data: Reason, balance info, decision time
- Reversal request: Async reversal trigger

**NFR Concerns**:
- **Latency (NFR-1)**: <1.5s total decision time
  - BIN lookup: <200ms
  - Preauth query: <600ms
  - Threshold calc: <50ms
  - Decision logic: <50ms
- **Availability (NFR-2)**: Fail-safe to DENY on processor error
- **Reliability (NFR-2)**: Circuit breaker, retry logic
- **Security (NFR-3)**: PCI-DSS compliance, tokenization
- **Compliance (NFR-5)**: Event logging for audit trail

**Key Algorithms**:
- BIN lookup (prepaid detection)
- Threshold calculation: `required = multiplier × basket_size`
- Balance comparison: `available ≥ required`
- Decision state machine (8 decision paths)

**Design Patterns**:
- Circuit Breaker (processor unavailability)
- Timeout & Retry (transient failures)
- Fallback Config (missing configuration)
- State Machine (decision logic)
- Async Reversal (non-critical path)

---

### 3. Configuration Service (Tier 2 - Support)

**Purpose**: Manage and distribute per-store authorization thresholds

**Boundaries**:
- **Upstream**: Operational team (updates)
- **Downstream**: Authorization Service (reads)

**Key Responsibilities**:
- Store per-location configuration (threshold multiplier, basket size)
- Provide configuration on-request
- Propagate configuration changes within 5 minutes
- Alert on missing configuration
- Support default values
- Apply validation rules

**Inputs**:
- Configuration requests: `{store_id}`
- Configuration updates: `{store_id, multiplier, basket_size}`
- Administrative actions: Create, update, delete

**Outputs**:
- Configuration response: `{store_id, multiplier, basket_size, ...}`
- Change events: Configuration update stream
- Alert events: Missing config alerts

**NFR Concerns**:
- **Latency (NFR-1)**: <100ms config retrieval (cached)
- **Ability (NFR-2)**: Defaults enable operation without configuration
- **Reliability**: Change propagation within 5 minutes
- **Compliance**: Change audit trail (who, what, when)

**Configuration Model**:
```json
{
  "store_id": "string (unique)",
  "threshold_multiplier": "2.0-10.0 (default: 3.0)",
  "average_basket_size": "number > 0 (default: 50.0)",
  "enabled": "boolean (default: true)",
  "created_timestamp": "ISO8601",
  "updated_timestamp": "ISO8601",
  "updated_by": "user/system"
}
```

**Default Values**:
```
threshold_multiplier: 3.0
average_basket_size: 50.0
```

---

### 4. Logging & Event Service (Tier 2 - Support)

**Purpose**: Capture and manage authorization events for audit and analytics

**Boundaries**:
- **Upstream**: Authorization Service (events)
- **Downstream**: Data Warehouse, Monitoring, Audit Trail

**Key Responsibilities**:
- Capture authorization events (approve, deny, error)
- Apply PCI-DSS compliant masking (no sensitive data)
- Publish events to event stream (async)
- Track decision metrics (latency, decision type)
- Maintain immutable audit trail
- Support event retention policies

**Inputs**:
- Authorization events: `{card_token, decision, balance, latency_ms, ...}`

**Outputs**:
- Event stream: Kafka/Queue topic for consumption
- Audit logs: Immutable transaction records
- Metrics: Counters for decision types
- Traces: Request tracing for debugging

**Event Schema**:
```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "request_id": "uuid",
  "store_id": "string",
  "decision": "APPROVED|DENIED_*",
  "card_last_4_hashed": "sha256",
  "card_token": "processor_token",
  "card_network": "VISA|MASTERCARD|...",
  "available_balance_cents": "number",
  "required_balance_cents": "number",
  "decision_time_ms": "number",
  "reason": "string"
}
```

**PCI-DSS Compliance**:
- ❌ NO: card_number, expiry, CVV
- ✅ YES: card_last_4_hashed, token, network, balance, decision

**NFR Concerns**:
- **PCI-DSS (NFR-3)**: Masking, no sensitive data
- **Compliance (NFR-5)**: 2-year retention, immutable
- **Latency (NFR-1)**: <10ms overhead on critical path (async)
- **Availability**: Failure doesn't block authorization

---

### 5. Payment Processor Integration (Tier 3)

**Purpose**: Interface with external payment processor for card operations

**Boundaries**:
- **Upstream**: Authorization Service (requests)
- **Downstream**: External payment processor API

**Key Responsibilities**:
- Tokenize card data
- Perform BIN lookups
- Initiate preauthorizations (balance holds)
- Query available balance
- Reverse preauthorizations
- Handle processor delays and errors
- Enforce timeouts and retries

**Inputs**:
- Card data: `{card_number, card_network}`
- Store ID: Transaction context
- Transaction amount: For preauth

**Outputs**:
- Tokens: Processor-issued card tokens
- BIN Lookup: `{card_type, network, is_prepaid}`
- Balance Response: `{status, available_balance, preauth_id}`
- Reversal Response: `{status, voided_amount}`

**Processor API Contract** (Typical):
```
POST /preauth/query
  Input: {card_token, amount, store_id}
  Output: {status, balance, preauth_id}
  Latency: <600ms (SLA)
  Timeout: 800ms

POST /preauth/reverse
  Input: {preauth_id}
  Output: {status, voided_amount}
  Latency: <200ms (SLA)
  Timeout: 600ms

GET /cards/bin/{bin}
  Input: {card_bin}
  Output: {card_type, network, is_prepaid}
  Latency: <100ms (SLA)
  Cache: 24-hour TTL
```

**NFR Concerns**:
- **Latency (NFR-1)**: <600ms balance query, <200ms reversal
- **Availability (NFR-2)**: Circuit breaker on processor errors
- **Reliability (NFR-2)**: Timeout, retry, fail-safe
- **Compliance (NFR-3)**: Tokenization, TLS 1.2+

**Resilience Patterns**:
- **Circuit Breaker**: Open on >50% errors, half-open test
- **Timeout**: 800ms max wait
- **Retry**: Single retry on transient errors (5xx, timeout)
- **Fallback**: Deny on persistent failure

---

### 6. Health & Monitoring (Tier 3 - Support)

**Purpose**: Observe and manage system health and performance

**Boundaries**:
- **Upstream**: All services (metrics)
- **Downstream**: Operational dashboards, alerting

**Key Responsibilities**:
- Collect metrics from all components
- Track circuit breaker state
- Calculate decision latency percentiles
- Monitor error rates
- Generate health check responses
- Trigger alerts on threshold breach
- Track component health status

**Metrics Collected**:
- **Latency**: Decision time (p50, p95, p99)
- **Throughput**: Decisions per second
- **Errors**: By type (processor error, timeout, etc.)
- **Success Rate**: Approval vs denial rate
- **Processor Health**: Success rate, latency
- **Configuration**: Missing config count
- **Circuit Breaker**: State transitions, open duration

**Alerts Triggered**:
- **Critical**: Processor unavailable (circuit open)
- **High**: Latency p95 > 1.5s for >5 minutes
- **High**: Error rate > 5% for >5 minutes
- **Medium**: Missing configuration detected
- **Medium**: Cache hit rate <90%

**NFR Concerns**:
- **Availability (NFR-2)**: Health checks guide failover
- **Reliability (NFR-2)**: Metrics drive resilience decisions
- **Monitoring**: Observable system behavior

**Health Check Endpoint**:
```json
GET /health
Response: {
  "status": "UP|DEGRADED|DOWN",
  "components": {
    "processor": {"status": "UP", "latency_ms": 150},
    "configuration": {"status": "UP", "cached_configs": 245},
    "database": {"status": "UP", "connections": 10},
    "authorization": {"status": "UP"}
  }
}
```

---

### 7. Data Warehouse Integration (Tier 3)

**Purpose**: Store and enable analysis of authorization events

**Boundaries**:
- **Upstream**: Event stream (from Logging Service)
- **Downstream**: Analytics, reporting, compliance

**Key Responsibilities**:
- Consume authorization events from stream
- Transform events to warehouse format
- Load events into analytics database
- Maintain data partitioning (by date)
- Enforce retention policies (2 years)
- Enable SQL-based querying
- Support compliance reporting

**Inputs**:
- Event stream: Authorization events (from Kafka)

**Outputs**:
- Warehouse tables: Partitioned by date
- Query results: Analytics and reports
- Compliance exports: Audit trail exports

**Warehouse Schema**:
```sql
CREATE TABLE entry_attempts (
  event_id UUID PRIMARY KEY,
  timestamp DATETIME NOT NULL,  -- partition key
  store_id STRING NOT NULL,     -- index
  decision STRING NOT NULL,     -- index
  card_network STRING,
  available_balance_cents INT64,
  required_balance_cents INT64,
  decision_time_ms INT,
  
  PARTITION BY DATE(timestamp)
)

Retention: 730 days (2 years)
```

**Analytics Queries**:
```sql
-- Approval rate by store (daily)
SELECT store_id, COUNT(*) total, 
  SUM(IF(decision='APPROVED', 1, 0)) approved,
  ROUND(100*approved/total, 2) approval_rate
FROM entry_attempts
WHERE DATE(timestamp) = CURRENT_DATE()
GROUP BY store_id

-- Latency analysis (hourly)
SELECT PERCENTILE_CONT(decision_time_ms, 0.50) p50,
       PERCENTILE_CONT(decision_time_ms, 0.95) p95,
       PERCENTILE_CONT(decision_time_ms, 0.99) p99
FROM entry_attempts
WHERE timestamp BETWEEN ...
```

**NFR Concerns**:
- **Compliance (NFR-5)**: 2-year retention, immutable
- **Data integrity**: All events captured, no loss
- **Query performance**: <5s for typical analytics

---

## NFR to Component Traceability Matrix

### NFR-1: Authorization Latency (<1.5s p95)

**Components Responsible**:
| Component | Responsibility | Target | Impact |
|-----------|-----------------|--------|--------|
| Entry Gate Interface | Card read → transmit | <100ms | Upstream delay |
| Authorization Service | Decision logic | <1100ms | Critical path |
| ├─ BIN Lookup | Prepaid check | <200ms | Early termination |
| ├─ Config Retrieval | Get thresholds | <100ms | Cached |
| ├─ Processor Query | Balance | <600ms | Largest component |
| ├─ Threshold Calc | Arithmetic | <50ms | Negligible |
| └─ Decision Logic | State machine | <50ms | Negligible |
| Payment Processor Integration | Enforce timeout | <600ms | External SLA |
| Logging & Event Service | Async capture | <10ms | Off critical path |

**Total Budget**: 100ms + 1100ms + 100ms = 1300ms (allows 200ms buffer)

**Optimization Strategies**:
1. ✅ Parallel fetch: Config + preauth together
2. ✅ Cache BIN (24-hour TTL)
3. ✅ Cache config (5-minute TTL)
4. ✅ Async logging (off-critical-path)
5. ✅ Async reversal (off-critical-path)
6. ✅ Early exit: BIN fails → immediate deny
7. ✅ Timeout enforcement: 800ms max per call

**Monitoring**:
- Track decision latency (p50, p95, p99) by store
- Alert if p95 > 1500ms sustained
- Dashboard metric priority

---

### NFR-2: Availability & Reliability (99%+ uptime, fail-safe degradation)

**Components Responsible**:

| Component | Responsibility | Strategy | Recovery |
|-----------|-----------------|----------|----------|
| Authorization Service | Core logic fault-tolerance | Defaults, fail-safe | Graceful deny |
| ├─ Processor Integration | External failure handling | Circuit breaker | Revert to closed |
| ├─ Configuration Service | Missing config handling | Defaults + alert | Use 3.0x, $50 |
| └─ Logging Service | Non-critical failures | Async, best-effort | Offline queuing |
| Entry Gate Interface | Network loss handling | Local fallback | Offline mode |
| Health & Monitoring | System observability | Metrics, health checks | Alerting |

**Failure Modes & Mitigations**:

| Failure | Component | Mitigation |
|---------|-----------|-----------|
| Processor down | Payment Integration | Circuit breaker → DENY_UNAVAILABLE |
| Processor slow (>600ms) | Payment Integration | Timeout → DENY_TIMEOUT |
| Config missing | Configuration Service | Use defaults (3.0x, $50) + alert |
| Config stale | Configuration Service | Stale config acceptable, <5min max |
| Logging fails | Logging Service | Silent failure, best-effort |
| Network partitioned | Entry Gate Interface | Offline mode, gate locked |
| Database down | Data Warehouse | Event queuing, later flush |

**Circuit Breaker Implementation**:
```
CLOSED (normal) 
  → Processor error rate > 50% for 60s 
  → OPEN (deny all) 
  → After 120s 
  → HALF-OPEN (test 1 request) 
    → Success → CLOSED 
    → Failure → OPEN
```

**Monitoring**:
- Processor success rate (target: 99%+)
- Circuit breaker state (track transitions)
- Config propagation delay (target: <5min)
- Logging event loss (target: 0%)

---

### NFR-3: PCI-DSS Compliance (No sensitive card data exposure)

**Components Responsible**:

| Component | Responsibility | Implementation |
|-----------|-----------------|-----------------|
| Entry Gate Interface | Input masking | Tokenize on collection |
| Authorization Service | Token usage | Use token, never card number |
| Payment Integration | Processor compliance | TLS 1.2+, tokenization |
| Logging & Event Service | Output masking | Mask sensitive fields |
| Data Warehouse | Storage protection | Tokenized only, no card |

**PCI-DSS Requirements & Implementation**:

| Requirement | What NOT to store | What to store | Implementation |
|-------------|-------------------|--------------|-----------------|
| No full card | card_number | card_last_4_hashed | SHA256 hash |
| No expiry | exp_month, exp_year | X | Never store |
| No CVV | cvv, cvc2 | X | Never capture |
| Encryption | X | card_token | TLS 1.2+ |
| Tokenization | Full card | token | Processor handles |
| Access control | X | Audit logs | RBAC + mTLS |
| Key management | X | Encryption keys | KMS per environment |

**Data Flow Diagram**:
```
[Card Reader] 
  → card_number 
  → [Tokenization] 
  → token + card_last_4_hashed 
  → Internal use only
  → [Event Logging] 
  → token + card_last_4_hashed (logged safely) 
  → [Data Warehouse] 
  → Analytics queries via token
  → [API Responses] 
  → Never expose card_number
```

**Audit Logging (Immutable)**:
- Every processor call (request/response, sans sensitive data)
- Every authorization decision (why approved/denied)
- Every config change (who, what, when)
- API access logs (who called what, when)
- 7-year retention (PCI requirement)

**Monitoring**:
- 0 occurrences of card_number in logs
- 0 API responses containing full card
- 100% of processor calls use TLS 1.2+
- All tokenization calls logged

---

### NFR-4: Geographic Scope (US Ptech Phase 1)

**Components Responsible**:

| Component | Responsibility | Implementation |
|-----------|-----------------|-----------------|
| Configuration Service | US validation | Validate store_id against US list |
| Authorization Service | Non-US handling | DENY with "not available" |
| Processor Integration | US endpoint | Limit to US processor region |
| Data Warehouse | US hosting | Regional database |

**Implementation**:
- Config validation: store_id must be in US ptech list
- Non-US store access: Authorization → DENY_NOT_AVAILABLE
- Monitor: Alert on non-US store attempts
- Phase 2 prep: Parameterize endpoints by region

---

### NFR-5: Data Retention & Logging (2-year min, immutable audit)

**Components Responsible**:

| Component | Responsibility | Implementation |
|-----------|-----------------|-----------------|
| Logging & Event Service | Event capture | Immutable write-once logs |
| Data Warehouse Integration | Retention policy | 730-day retention |
| Database | Archival | Automated cleanup after 2 years |

**Retention Policy**:
```
Day 0-30:    Hot storage (fast queries)
Day 31-365:  Warm storage (slower queries)
Day 365-730: Cold storage (archive)
Day 731+:    Delete (or legal hold if needed)
```

**Immutable Audit Trail**:
- Write-once event logs
- No update/delete of past events
- Append-only event stream
- Signed/hashed records (tamper detection)
- Access audit (who queried what)

**Compliance Reporting**:
- Generate cardholder disputes: By request_id, timestamp
- Regulatory reports: Authorization volumes, approval rates
- Fraud analysis: By card, store, decision type
- SLA reporting: Latency metrics by store

**Monitoring**:
- Event ingestion rate (target: 100%+ of authorizations)
- Event loss (target: 0%)
- Retention policy enforcement (target: automatic)
- Query audit trails (log all analytical queries)

---

## Component-Level NFR Implementations

### Authorization Service - Latency Optimization

**Latency Budget Breakdown**:
```
Total: <1500ms (p95)

External Calls (parallelizable):
  BIN Lookup:      0-200ms
  Processor Query: 50-600ms (parallel with config)
  Config Fetch:    10-100ms (cached, parallel)
  
Internal Operations:
  Card Input:      <10ms
  Decision Logic:  <50ms
  Threshold Calc:  <50ms
  Event Log:       <10ms (async)
  Reversal Init:   <10ms (async)
  
Total (parallel): 0-600ms processor + 10-100ms config = 610-700ms
Latency Addition: 50ms overhead
Total: ~650-750ms (well under 1500ms target)
```

**Optimization Patterns**:
1. **Parallel Execution**: Fetch config + initiate processor call together
2. **Caching**: BIN cache (24h), Config cache (5m)
3. **Early Termination**: Return DENY_NOT_PREPAID immediately
4. **Async Operations**: Log + reversal off critical path
5. **Timeout Management**: 800ms cap per external call

**Code Pattern** (Pseudocode):
```java
authorize(cardData, storeId) {
  startTime = now()
  
  // Parallel: BIN lookup + config fetch
  binLookup = async call lookupBIN(cardData)
  config = configService.get(storeId)  // cached, ~5-10ms
  
  // Check prepaid early
  if (!binLookup.isPrepaid()) return DENY_NOT_PREPAID
  
  // Processor query (critical path)
  balance = processorClient.queryBalance(...)  // timeout: 800ms
  if (!balance.success()) return DENY_PROCESSOR_ERROR
  
  // Decision (fast arithmetic)
  required = config.multiplier * config.basketSize
  decision = balance.available >= required ? APPROVE : DENY
  
  // Async (off critical path)
  async {
    eventLogger.log(decision)
    if (DENY) processorClient.reverse(balance.preauthId)
  }
  
  return decision
}
```

**Performance Monitoring Code**:
```java
@Timed(name = "authorization.decision.time")
public AuthorizationResponse authorize(...) { ... }

// Metrics exported:
- authorization.decision.time (histogram)
  - p50, p95, p99
  - per-store tags
  - decision-type tags
```

### Configuration Service - Cache Design

**Cache Architecture**:
```
Layer 1: In-Memory Cache (5-min TTL)
├─ Store: ConcurrentHashMap<store_id, config>
├─ Size: ~1MB (1000 stores × 1KB each)
├─ Hit Rate Target: >95%
└─ Latency: ~2-5ms

Layer 2: Database (PostgreSQL)
├─ Store: configurations table
├─ Index: store_id (PK)
├─ Fallback: On cache miss
└─ Latency: ~20-50ms

Layer 3: Defaults (In-Code)
├─ multiplier: 3.0
├─ basketSize: 50.0
└─ Alert: On default usage
```

**Cache Replacement Policy**:
- TTL: 5 minutes (automatic expiration)
- Size: LRU if memory constrained
- Invalidation: On update, clear key

**Cache Invalidation**:
```java
updateConfig(storeId, newConfig) {
  // Update database first
  database.update(storeId, newConfig)
  
  // Invalidate cache
  cache.invalidate(storeId)
  
  // Publish change event
  eventBus.publish(ConfigChanged(storeId, newConfig))
  
  // Propagate to subscribers (async)
  // Service instances receive event, invalidate local cache
}
```

### Payment Processor Integration - Resilience

**Resilience Pattern Stack**:
```
Authorization Request
  ▼
[Timeout Manager: 800ms max]
  ├─ Success → Return response
  ├─ Timeout → TimeoutException
  └─ Network Error → Exception
    ▼
[Retry Logic: 1 attempt max]
  ├─ Retry if: 5xx, timeout, connection error
  ├─ No retry if: 4xx, validation error
  └─ Backoff: 100ms + jitter
    ▼
[Circuit Breaker: Fail-safe]
  ├─ Track error rate (window: 1 minute)
  ├─ Open if: >50% errors
  ├─ Half-Open: Test 1 request after 2 min
  └─ Closed: Return to normal
    ▼
[Error Handling & Mapping]
  ├─ 5xx → DENIED_PROCESSOR_ERROR
  ├─ Timeout → DENIED_TIMEOUT
  ├─ Connection → DENIED_PROCESSOR_ERROR
  └─ Other → DENIED_PROCESSOR_ERROR
```

**Implementation Pseudocode**:
```java
public BalanceQueryResponse queryBalance(BalanceQueryRequest req) {
  startTime = now()
  
  try {
    // Attempt with timeout
    future = httpClient.post(processorUrl, req, timeout: 800ms)
    response = future.get(timeout: 800ms)
    
    // Success path
    circuitBreaker.record(SUCCESS)
    return response
    
  } catch (TimeoutException e) {
    circuitBreaker.record(ERROR)
    throw ProcessorTimeoutException(e)
    
  } catch (Exception e) {
    circuitBreaker.record(ERROR)
    
    // Trigger retry on transient error
    if (isTransient(e)) {
      return retry(req)
    } else {
      throw ProcessorErrorException(e)
    }
  }
}

private BalanceQueryResponse retry(BalanceQueryRequest req) {
  // Exponential backoff: 100ms + jitter
  wait(100 + random(0-100))
  
  try {
    return queryBalance(req)  // 2nd attempt
  } catch (Exception e) {
    // Give up after retry
    throw e
  }
}
```

### Logging Service - PCI-DSS Masking

**Masking Pipeline**:
```
Raw Event
  {card_number: "4111111111111111", 
   card_network: "VISA",
   decision: "APPROVED",
   balance: 20000}
  ▼
[Field Selection: What to log]
  ├─ Keep: decision, balance, latency
  ├─ Remove: card_number, expiry, CVV
  └─ Transform: card_last_4_hashed
    ▼  
[Data Masking: Transform sensitive values]
  ├─ card_number → remove (never log)
  ├─ card_last_4 → SHA256 hash
  ├─ card_network → keep as-is (not sensitive)
  └─ balance → keep (public)
    ▼
[Encryption: In-transit & at-rest]
  ├─ TLS 1.2+ for API calls
  ├─ Encrypted database connections
  └─ Encrypted warehouse storage
    ▼
Safe Event Log
  {card_last_4_hashed: "a1b2c3...",
   card_network: "VISA",
   decision: "APPROVED",
   balance: 20000}
```

**Implementation Pseudocode**:
```java
public void logAuthorizationEvent(AuthorizationResponse response) {
  // Build safe event (never includes sensitive data)
  event = AuthorizationEvent.builder()
    .eventId(UUID.randomUUID())
    .timestamp(now())
    .requestId(response.getRequestId())
    .decision(response.getDecision())
    .cardNetwork(response.getCardNetwork())
    .cardLast4Hashed(sha256(response.getCardLast4()))
    .cardToken(response.getCardToken())  // Processor token, not card #
    .availableBalance(response.getAvailableBalance())
    .requiredBalance(response.getRequiredBalance())
    .decisionTime(response.getDecisionTime())
    .build()
  
  // Validate no sensitive data
  validateNoCardNumbers(event)
  validateNoExpiry(event)
  validateNoCVV(event)
  
  // Publish to queue (async)
  queue.publish(event)
  
  // Log to audit trail (immutable)
  auditLog.append(event)
}

private void validateNoCardNumbers(AuthorizationEvent event) {
  String eventJson = event.toJson()
  if (eventJson.matches("4[0-9]{12}(?:[0-9]{3})")) {
    throw PCI_VIOLATION("Card number found in event!")
  }
}
```

---

## Traceability Summary

### Components → NFRs Matrix

```
                    NFR-1  NFR-2  NFR-3  NFR-4  NFR-5
                    (Lat)  (Avail)(PCI)  (Geo)  (Ret)
                    ─────  ─────  ─────  ─────  ─────
Entry Gate            ████    ██
Authorization        ██████  ██████        ████
├─ BIN Lookup         ████
├─ Processor          ██████  ██████  ████  
├─ Configuration       ██    ██       
└─ Decision           ██    
  
Configuration        ██    ██              ██
Logging              ██    ██    ██████          ██████
Payment Processor    ██████  ██████  ████  
  
Health & Monitor      ██    ██████        
Warehouse                                        ██████
```

**Legend**: 
- ██ = Minor responsibility
- ████ = Primary responsibility
- ██████ = Critical responsibility

---

**Document Version**: 1.0  
**Date**: March 16, 2026  
**Status**: Ready for Design Review  
**Next Step**: Component detailed design & API specifications
