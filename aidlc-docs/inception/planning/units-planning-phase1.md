# JWO Prepaid Balance Check - Phase 1 Units Planning

**Development Units Definition & Sequencing**

**Version**: 1.0  
**Date**: March 16, 2026  
**Project**: JWO Prepaid Card Balance Check - Phase 1 MVP  
**Phase**: Units Planning  
**Target Audience**: Engineering Leads, Project Manager, Tech Leads

---

## Table of Contents

1. [Units Planning Overview](#units-planning-overview)
2. [Development Units (Detailed)](#development-units-detailed)
3. [Unit Dependencies & Sequencing](#unit-dependencies--sequencing)
4. [Development Timeline](#development-timeline)
5. [Effort Estimates & Resource Allocation](#effort-estimates--resource-allocation)
6. [Risk Assessment & Mitigations](#risk-assessment--mitigations)
7. [Testing Strategy by Unit](#testing-strategy-by-unit)
8. [Deployment & Rollout Plan](#deployment--rollout-plan)

---

## Units Planning Overview

### Strategy
- **Total Units**: 11 development units organized into 5 service layers
- **Approach**: 
  - **Layer 1**: Foundational services (Config, Logging, integration adapters)
  - **Layer 2**: Core business logic (Authorization Service)
  - **Layer 3**: Integration points (Gate Interface, end-to-end flows)
  - **Layer 4**: Operational capabilities (Monitoring, alerts)
  
- **Parallelization**: Units can be developed in parallel by multiple teams with clear interfaces
- **MVP Completion**: 20-28 weeks (5-7 months) with 4-6 engineers
- **Critical Dependencies**: 
  - Processor API spec (blocker for Unit-2)
  - Gate hardware integration details (blocker for Unit-10)

### Unit Sizing
- **Small Unit** (S): 1-2 weeks, 1-2 engineers
- **Medium Unit** (M): 2-3 weeks, 2-3 engineers  
- **Large Unit** (L): 3-4 weeks, 3-4 engineers
- **Extra Large** (XL): 4-5 weeks, 4-5 engineers

---

## Development Units (Detailed)

### Layer 1: Foundational Services (Lowest Dependencies)

---

#### **Unit-1: Configuration Service - Core**

**Dependency**: None (standalone)

**Responsibility**:
- Store per-store configuration (threshold_multiplier, average_basket_size)
- Default values (3x multiplier, $50 basket)
- CRUD operations for config

**Components**:
- PostgreSQL schema for configurations
- Config repository (data access layer)
- Configuration model classes
- In-memory cache initialization

**Key Deliverables**:
- Config table schema + migrations
- ConfigRepository class (CRUD)
- ConfigService class (business logic)
- Default values constants
- Unit tests (repository, edge cases)

**Implementation Details**:
```
Inputs:
  - store_id (string)
  - threshold_multiplier (float)
  - average_basket_size (decimal)

Outputs:
  - Config object with all fields
  - Defaults if not found

Validation:
  - threshold_multiplier: 0.5 - 10.0 (required)
  - average_basket_size: > 0 (required)
  - store_id: non-empty (required)
```

**Testing**:
- ✅ Create config, verify stored correctly
- ✅ Get existing config, verify retrieval
- ✅ Get missing config, verify defaults returned
- ✅ Update config, verify changes persist
- ✅ Update with invalid data, verify validation error
- ✅ Concurrent updates, verify no lost updates

**Est. Effort**: **2 weeks (Small)** | 1-2 engineers

**Success Criteria**:
- [ ] All CRUD operations working
- [ ] Validation prevents invalid data
- [ ] Defaults work correctly
- [ ] Tests achieve 90%+ coverage
- [ ] <50ms retrieval latency (local cache)

---

#### **Unit-2: Payment Processor Integration Layer**

**Dependency**: Processor API spec (BLOCKER)

**Responsibility**:
- Abstract payment processor API
- Tokenize card data
- Handle preauth + balance query
- Handle preauth reversal
- Error handling + timeouts

**Components**:
- PaymentProcessorClient interface (abstraction)
- Concrete processor implementation
- Token storage/retrieval
- Timeout + retry logic
- Error code mapping

**Key Deliverables**:
- PaymentProcessorClient interface
- ProcessorApiClient implementation
- BINLookupService (card classification)
- BalanceQueryService
- PreauthReversalService
- TokenizationService
- Error mapping + handling
- Unit tests + mock processor

**Implementation Details**:
```
Methods:
  1. queryBalance(cardData, amount) 
     → {status, available_balance, preauth_id, error}
     → SLA: <600ms, timeout: 800ms
  
  2. reversePreauth(preauth_id) 
     → {status, voided_amount, error}
     → SLA: <200ms, timeout: 600ms
  
  3. lookupBIN(cardNumber) 
     → {card_type, network, is_prepaid}
     → Cache locally, expire daily

Security:
  - Tokenize card_number → token (never store full number)
  - Only store/log: {card_last_4_hashed, token}
  - TLS 1.2+ for all calls
  - Timeout all calls (800ms max)
```

**Testing**:
- ✅ Successful balance query
- ✅ Balance query timeout (after 800ms)
- ✅ Balance query error response
- ✅ Preauth without balance (fail-safe)
- ✅ Reversal success
- ✅ Reversal timeout
- ✅ Card tokenization (card number encrypted)
- ✅ BIN lookup hit/miss
- ✅ Mock processor for testing

**Est. Effort**: **3-4 weeks (Large)** | 2-3 engineers

**Blocker**: ⚠️ **Must have processor API spec by end of March**

**Success Criteria**:
- [ ] All processor APIs wrapped
- [ ] Timeouts working (<10 failed timeouts in test)
- [ ] Tokenization prevents full card exposure
- [ ] <600ms latency on balance query (p95)
- [ ] Mock processor enables offline testing
- [ ] Tests achieve 95%+ coverage

---

#### **Unit-3: Logging Service - Event Capture**

**Dependency**: None (standalone)

**Responsibility**:
- Capture authorization events
- Store to data warehouse
- Filter sensitive data (PCI-DSS)
- Queue events for async processing

**Components**:
- Event model classes
- Event serialization (JSON)
- Event repository (to warehouse)
- Message queue producer
- PCI-DSS data masking
- Async event handler

**Key Deliverables**:
- Event schema classes (approval, denial, error, etc.)
- EventLogger interface
- EventRepository (warehouse writer)
- MessageQueue producer config
- Data masking/tokenization logic
- Unit tests + mock warehouse

**Sensitive Data Handling**:
```
NEVER log:
  - card_number (use token only)
  - card_expiry
  - cardholder_name

ALWAYS log:
  - card_last_4_hashed (SHA256)
  - card_network
  - card_token (processor token)
  - timestamp
  - decision result
  - available_balance
  - required_balance
```

**Testing**:
- ✅ Event created with all fields
- ✅ Event serialized to JSON
- ✅ Event sent to queue
- ✅ Card number NOT in event (tokenized)
- ✅ Sensitive fields hashed/masked
- ✅ Event retrieval from warehouse
- ✅ High-volume event handling (1000 events/sec)

**Est. Effort**: **2-3 weeks (Medium)** | 1-2 engineers

**Success Criteria**:
- [ ] All event types captured
- [ ] No sensitive data in logs
- [ ] <100ms logging overhead on authorization path
- [ ] Queue handles 1000+ events/sec
- [ ] 2-year retention verified
- [ ] Tests achieve 90%+ coverage

---

### Layer 2: Core Business Logic

---

#### **Unit-4: Authorization Service - Core Logic**

**Dependency**: Unit-1 (Configuration), Unit-2 (Processor), Unit-3 (Logging)

**Responsibility**:
- BIN lookup + prepaid classification
- Config retrieval
- Balance query orchestration
- Threshold calculation
- Approval/denial decision
- Preauth reversal initiation
- Call coordination

**Components**:
- AuthorizationService (main orchestrator)
- DecisionEngine (logic)
- ThresholdCalculator
- BINClassifier
- ErrorHandler
- CircuitBreaker

**Key Deliverables**:
- AuthorizationService class
- DecisionEngine with state machine
- Threshold calculation logic
- BIN lookup integration
- Circuit breaker implementation
- Error handling matrix
- Unit tests + integration tests

**Core Algorithm**:
```pseudocode
authorize(cardData, storeId):
  1. binLookup(cardData) → is_prepaid?
     IF NOT prepaid: DENY_NOT_PREPAID
  
  2. getConfig(storeId) → config or defaults
     IF missing: LOG alert, USE defaults
  
  3. queryBalance(cardData, calculateRequired(config))
     IF timeout: DENY_TIMEOUT
     IF error: DENY_ERROR
     IF no_balance: DENY_NO_BALANCE
  
  4. calculateRequired = config.multiplier × config.basket_size
     available = response.balance
  
  5. IF available >= required: APPROVE
     ELSE: initiateReversal(); DENY_INSUFFICIENT
  
  6. Log decision event
  7. Return decision to gate
```

**Latency Budget**:
- BIN lookup: <200ms
- Config retrieval: <100ms (cached)
- Balance query: <600ms
- Threshold calc: <50ms
- Decision logic: <50ms
- Reversal initiate: <200ms
- **Total**: <1200ms (p95)

**Testing**:
- ✅ Happy path (sufficient balance)
- ✅ Insufficient balance
- ✅ Not prepaid card
- ✅ Processor timeout
- ✅ Processor error
- ✅ Missing balance
- ✅ Missing config (use defaults)
- ✅ Config exists (use config)
- ✅ Reversal initiation
- ✅ Latency <1200ms
- ✅ All error paths logged correctly
- ✅ Concurrent requests handled correctly

**Est. Effort**: **3-4 weeks (Large)** | 2-3 engineers

**Success Criteria**:
- [ ] All decision paths working (8 paths tested)
- [ ] Latency <1200ms (p95)
- [ ] All errors logged with context
- [ ] Circuit breaker activates correctly
- [ ] Reversal initiated within 100ms
- [ ] Tests achieve 95%+ coverage
- [ ] Load test: 100+ decisions/sec

---

#### **Unit-5: Authorization Service - Resilience & Monitoring**

**Dependency**: Unit-4 (core logic), Unit-3 (logging)

**Responsibility**:
- Circuit breaker state management
- Retry logic (transient errors)
- Timeout enforcement
- Health checks
- Metrics collection
- Error tracking

**Components**:
- CircuitBreakerManager
- RetryPolicy
- TimeoutManager
- HealthChecker
- MetricsCollector
- ErrorTracker

**Key Deliverables**:
- CircuitBreaker implementation
- Retry policy configuration
- Timeout wrapper for all calls
- Health check endpoints
- Metrics aggregation
- Error trend analysis
- Unit + integration tests

**Circuit Breaker State Machine**:
```
CLOSED → OPEN: Error rate > 50% in 1 minute
OPEN → HALF_OPEN: After 2 minutes
HALF_OPEN → CLOSED: Test request succeeds
HALF_OPEN → OPEN: Test request fails

Behavior:
  CLOSED: Forward requests normally
  OPEN: FAIL_FAST with DENY decision
  HALF_OPEN: Allow single test request
```

**Metrics Tracked**:
- Decision latency (p50, p95, p99)
- Approval rate
- Denial breakdown (by reason)
- Error rate
- Processor success rate
- Circuit breaker state
- Reversal success rate

**Testing**:
- ✅ Circuit breaker state transitions
- ✅ Fail-fast on open circuit
- ✅ Recovery on success in half-open
- ✅ Retry on transient error (once)
- ✅ Timeout after 800ms max
- ✅ Metrics collection accuracy
- ✅ Health check endpoint
- ✅ High error rate detection

**Est. Effort**: **2-3 weeks (Medium)** | 1-2 engineers

**Success Criteria**:
- [ ] Circuit breaker working correctly
- [ ] <1% unhandled errors
- [ ] Metrics collected with <100ms overhead
- [ ] Health check endpoint responds in <100ms
- [ ] Timeouts enforced on all external calls
- [ ] Retry logic reduces transient errors by 80%+

---

### Layer 3: Integration & Interfaces

---

#### **Unit-6: Entry Gate Interface - Adapter**

**Dependency**: Unit-4 (Authorization)

**Responsibility**:
- Hardware adapter (card reader, display, gate control)
- Card data normalization
- Request/response conversion
- Display message routing
- Gate command execution
- Offline resilience

**Components**:
- HardwareAdapter interface
- CardReaderAdapter
- DisplayAdapter
- GateControllerAdapter
- RequestNormalizer
- MessageRouter
- OfflineModeHandler

**Key Deliverables**:
- Hardware adapter interfaces
- Card data parser
- Request/response mapping
- Display message templates
- Gate command executor
- Offline handling logic
- Hardware simulation for testing

**Hardware Integration Points**:
```
INPUT (from hardware):
  - Card reader event: {card_number, card_network, card_last_4}
  
  - Gate sensors: {cardholder_present, gate_position, door_open}

OUTPUT (to hardware):
  - Display message: {text, color, duration}
  - Gate control: {open, close, keep_closed}

Hardware Constraints:
  - <100ms response to card read
  - Display message <200ms
  - Gate movement 1-2 seconds (hardware latency)
```

**Offline Resilience**:
- Cache last working config
- Retry auth requests with backoff
- Local failsafe: gate closed on persistent failure
- Alert ops on network issues

**Testing**:
- ✅ Card read → normalization
- ✅ Authorization response → gate command
- ✅ Denial → gate closed
- ✅ Approval → gate open
- ✅ Display messages render correctly
- ✅ Offline handling (no network)
- ✅ Network recovery
- ✅ Sensor inputs handled
- ✅ Hardware simulation works

**Est. Effort**: **2-3 weeks (Medium)** | 1-2 engineers

**Blocker**: ⚠️ **Hardware integration details needed (GPIO? REST API? Proprietary protocol?)**

**Success Criteria**:
- [ ] Card data parsed correctly
- [ ] Authorization requests sent correctly
- [ ] Gate commands executed correctly
- [ ] Display shows appropriate messages
- [ ] Offline handling works (gate closed)
- [ ] <100ms response to card read
- [ ] Hardware simulation enables development without physical hardware

---

#### **Unit-7: Configuration Service - API & Propagation**

**Dependency**: Unit-1 (core config), Unit-4 (consumption)

**Responsibility**:
- REST API for config management
- Configuration change propagation
- Cache invalidation
- Real-time updates
- Distributed cache synchronization

**Components**:
- ConfigController (REST endpoints)
- ConfigChangePublisher (event streaming)
- DistributedCache (Redis)
- CacheInvalidator
- ChangeValidator
- AuditLogger

**Key Deliverables**:
- REST API endpoints (GET, POST, PUT)
- Input validation
- Change event streaming
- Distributed cache with TTL
- Change notification to Authorization Service
- API tests + integration tests
- Documentation

**REST API Endpoints**:
```
GET /config/store/{store_id}
  → Returns current config or defaults
  
POST /config/store/{store_id}
  → Creates new store config
  → Validates inputs
  → Publishes change event
  
PUT /config/store/{store_id}
  → Updates existing config
  → Validates inputs
  → Publishes change event
  
GET /config/health
  → Returns service health
```

**Propagation Model**:
```
Config Update:
  1. Validate new config
  2. Store to PostgreSQL
  3. Publish to event stream (Kafka)
  4. Invalidate local cache
  
Change Reception (Authorization Service):
  1. Consume change event from stream
  2. Update local cache
  3. Log change event
  
Cache Behavior:
  - Direct API calls: Always get latest
  - Cached access: <5 min TTL, fall back to defaults
```

**Testing**:
- ✅ GET returns current config
- ✅ POST creates new config
- ✅ PUT updates existing config
- ✅ Validation prevents bad data
- ✅ Change event published to stream
- ✅ Cache invalidated on update
- ✅ Change propagated to subscribers
- ✅ Concurrent updates handled
- ✅ API tests + integration tests

**Est. Effort**: **2-3 weeks (Medium)** | 2 engineers

**Success Criteria**:
- [ ] All REST operations working
- [ ] Input validation working
- [ ] Changes propagated <5 minutes
- [ ] Cache consistency maintained
- [ ] API responds in <50ms (cached)
- [ ] Tests achieve 90%+ coverage
- [ ] API documentation complete

---

#### **Unit-8: Authorization Service - REST API**

**Dependency**: Unit-4 (core logic), Unit-5 (resilience)

**Responsibility**:
- REST endpoint for authorization
- Request validation
- Response formatting
- Error handling
- API documentation

**Components**:
- AuthorizationController
- RequestValidator
- ResponseFormatter
- ErrorHandler

**Key Deliverables**:
- REST endpoint: POST /authorize/check-entry
- Request/response DTOs
- Validation logic
- Error handling
- API tests

**REST Endpoint**:
```
POST /authorize/check-entry

Request:
{
  "store_id": "store-123",
  "card_data": {
    "card_number": "encrypted",
    "card_network": "visa",
    "card_last_4": "1234"
  },
  "request_id": "uuid"
}

Response (Approved):
{
  "decision": "approved",
  "available_balance_cents": 17500,
  "required_balance_cents": 15000,
  "total_decision_time_ms": 520
}

Response (Denied):
{
  "decision": "denied_insufficient",
  "available_balance_cents": 12500,
  "required_balance_cents": 15000,
  "reason": "Available < Required"
}

HTTP Status:
  200: Decision made (check decision field)
  400: Bad request
  408: Timeout
  503: Service unavailable
```

**Testing**:
- ✅ Valid request → 200 with decision
- ✅ Invalid data → 400 error
- ✅ Timeout → 408 error
- ✅ Service down → 503 error
- ✅ Response format correct
- ✅ Error messages clear

**Est. Effort**: **1-2 weeks (Small)** | 1 engineer

**Success Criteria**:
- [ ] Endpoint returns correct responses
- [ ] HTTP status codes correct
- [ ] Response format matches spec
- [ ] Validation working
- [ ] API tests passing
- [ ] API documentation complete

---

### Layer 4: Operational Capabilities

---

#### **Unit-9: Monitoring & Real-Time Dashboard**

**Dependency**: Unit-3 (logging), Unit-4 (authorization metrics)

**Responsibility**:
- Real-time metrics dashboard
- 5-minute lag latency
- Performance trend tracking
- Operational alerts
- Health status display

**Components**:
- MetricsAggregator
- DashboardBackend
- AlertingEngine
- TrendAnalyzer
- HealthMonitor

**Key Deliverables**:
- Metrics aggregation service
- Dashboard UI (simple web interface)
- Alert rule engine
- Trend detection
- Health check page
- Tests + integration

**Dashboard Metrics**:
```
Real-Time (5-min window):
  - Total transactions
  - Approval rate (%)
  - Denial breakdown (insufficient, timeout, error, etc.)
  - Average decision latency (p50, p95, p99)
  - System error rate
  - Processor health

Per-Store Metrics:
  - Store transaction count
  - Store approval rate
  - Store average balance
  - Store error rate

Alerts:
  🔴 High latency (p95 > 1500ms, sustained 5 min)
  🔴 High error rate (> 5%, sustained 5 min)
  🟡 Missing config (detected, ops action needed)
  🔴 Processor unavailable (circuit open)
```

**Testing**:
- ✅ Metrics aggregation accuracy
- ✅ Dashboard data freshness (<5 min lag)
- ✅ Alert triggering on threshold breach
- ✅ Trend detection accuracy
- ✅ Health check endpoint
- ✅ High-volume metrics (1000+ events/sec)

**Est. Effort**: **2-3 weeks (Medium)** | 1-2 engineers

**Success Criteria**:
- [ ] Dashboard displays correctly
- [ ] Metrics accurate within 5 minutes
- [ ] Alerts triggering correctly
- [ ] Trends detected accurately
- [ ] Health page responds <100ms
- [ ] Handles 1000+ events/sec

---

#### **Unit-10: Data Warehouse & Analytics**

**Dependency**: Unit-3 (logging - event ingestion)

**Responsibility**:
- Data warehouse setup
- Event storage
- Data partitioning
- Query optimization
- Compliance data retention
- Analytics enables

**Components**:
- Data warehouse schema (BigQuery/Snowflake)
- Event ETL pipeline
- Partitioning strategy
- Index optimization
- Access controls
- Spark/BigQuery jobs

**Key Deliverables**:
- Data warehouse schema design
- Event ingestion pipeline
- Data partitioning (by date)
- Query templates for analytics
- Compliance automation
- Documentation

**Data Model**:
```
Table: entry_attempts
  Columns:
    - event_id (primary key)
    - timestamp (partition key)
    - store_id (index)
    - decision (index)
    - available_balance_cents
    - required_balance_cents
    - decision_time_ms
    - request_id (unique)

Retention: 2 years (730 days)
Partitioning: By date (YYYY-MM-DD)
Indexes: store_id, timestamp, decision
```

**Sample Queries**:
```sql
-- Approval rate by store
SELECT store_id, 
       COUNT(*) total,
       SUM(CASE WHEN decision = 'approved' THEN 1 ELSE 0 END) approved,
       ROUND(100.0 * SUM(CASE WHEN decision = 'approved' THEN 1 ELSE 0 END) / COUNT(*), 2) approval_rate
FROM entry_attempts
WHERE date(timestamp) = CURRENT_DATE()
GROUP BY store_id
ORDER BY approval_rate DESC;

-- Latency analysis
SELECT PERCENTILE_CONT(decision_time_ms, 0.5) as p50,
       PERCENTILE_CONT(decision_time_ms, 0.95) as p95,
       PERCENTILE_CONT(decision_time_ms, 0.99) as p99
FROM entry_attempts
WHERE date(timestamp) = CURRENT_DATE();
```

**Testing**:
- ✅ Events ingested correctly
- ✅ Data partitions created
- ✅ Queries execute <5s (for typical analytics)
- ✅ 2-year retention enforced
- ✅ Data integrity checks pass

**Est. Effort**: **2-3 weeks (Medium)** | 1-2 engineers

**Success Criteria**:
- [ ] Schema designed for analytics
- [ ] Event ingestion working <5 min lag
- [ ] Partitions created automatically
- [ ] Sample queries execute <5s
- [ ] 2-year retention policy automated
- [ ] Access controls configured

---

#### **Unit-11: End-to-End Integration & System Testing**

**Dependency**: All units (1-10)

**Responsibility**:
- Integrate all components
- End-to-end testing
- Performance testing
- Security testing (OWASP top 10)
- Load testing
- Compliance validation

**Components**:
- Test harness
- End-to-end test suite
- Performance test suite
- Security scanning tools
- Load testing framework
- Compliance checklist

**Key Deliverables**:
- E2E test scenarios (happy path, error paths)
- Performance test suite (latency, throughput)
- Security testing (tokenization, encryption, injection)
- Load testing (100+ req/sec, sustained)
- Compliance checklist (PCI-DSS, data retention, etc.)
- Documentation

**E2E Test Scenarios**:
```
Happy Path:
  1. Customer presents prepaid card
  2. System checks BIN → prepaid ✓
  3. System gets balance → $175 ✓
  4. System gets config → 3x, $50
  5. Required = $150 ✓
  6. $175 >= $150 → APPROVE
  7. Gate opens ✓
  8. Event logged ✓

Error Paths:
  - Timeout handling (processor down)
  - Missing balance (fail-safe)
  - Missing config (use defaults)
  - Not prepaid card (deny)
  - Insufficient funds (deny + reverse)
```

**Performance Testing**:
```
Baseline Requirements (Phase 1 Target):
  - Latency p95: <1500ms
  - Throughput: 100+ decisions/sec
  - Approval decisions: 60-70%
  - Error rate: <1%
  - System availability: >99%
```

**Security Testing**:
```
Checks:
  ✓ Card number not logged (tokenization)
  ✓ TLS 1.2+ on all APIs
  ✓ No SQL injection vectors
  ✓ No XSS vulnerabilities
  ✓ Timeout enforcement (DOS prevention)
  ✓ Access control (RBAC)
  ✓ Input validation (all fields)
```

**Testing**:
- ✅ E2E happy path
- ✅ E2E error paths (8 scenarios)
- ✅ Performance meets targets
- ✅ Load test 100+ req/sec sustained
- ✅ No security vulnerabilities
- ✅ Data retention verified
- ✅ PCI-DSS compliance confirmed

**Est. Effort**: **3-4 weeks (Large)** | 2-3 engineers

**Success Criteria**:
- [ ] All E2E tests passing
- [ ] Latency p95 < 1500ms
- [ ] Throughput 100+ req/sec
- [ ] No security vulnerabilities found
- [ ] Load test passed
- [ ] PCI-DSS compliance verified
- [ ] Ready for pilot

---

## Unit Dependencies & Sequencing

### Dependency Graph

```
Unit-1 (Config Core)
    ├── Unit-7 (Config API)
    │   └── Unit-4 (Auth Service Core) ──┐
    │       ├── Unit-5 (Auth Resilience) ─┤
    │       ├── Unit-8 (Auth API) ────────┤─→ Unit-11 (E2E Testing)
    │       └── Unit-6 (Gate Interface) ──┤
    │
    ├── Unit-2 (Processor Integration) 
    │   └── Unit-4 (Auth Service Core)
    │
    ├── Unit-3 (Logging)
    │   ├── Unit-4 (Auth Service Core)
    │   ├── Unit-9 (Monitoring)
    │   └── Unit-10 (Data Warehouse)
    │
    └── Unit-10 (Data Warehouse)
```

### Development Sequence (Critical Path)

**Phase 1: Foundational (Weeks 1-4)**
- ✅ Unit-1: Configuration Service - Core (2 weeks, starts immediately)
- ✅ Unit-2: Processor Integration (3-4 weeks, blocked on Processor API spec)
- ✅ Unit-3: Logging Service (2-3 weeks, parallel with Unit-1)

**Phase 2: Core Logic (Weeks 5-9)**
- ✅ Unit-4: Authorization Service - Core (3-4 weeks, depends on Unit-1,2,3)
- ✅ Unit-5: Authorization Service - Resilience (2-3 weeks, parallel with Unit-4)
- 🔄 Unit-7: Config Service - API (2-3 weeks, parallel with Unit-4)

**Phase 3: Integration (Weeks 10-13)**
- ✅ Unit-8: Authorization Service - REST API (1-2 weeks, depends on Unit-4,5)
- ✅ Unit-6: Gate Interface - Adapter (2-3 weeks, depends on Unit-4, blocked on hardware details)

**Phase 4: Operations (Weeks 14-18)**
- ✅ Unit-9: Monitoring & Dashboard (2-3 weeks, depends on Unit-3,4)
- ✅ Unit-10: Data Warehouse (2-3 weeks, depends on Unit-3)

**Phase 5: System Testing (Weeks 19-22)**
- ✅ Unit-11: E2E Integration & Testing (3-4 weeks, depends on all units)

### Parallelization Opportunities

**Can start immediately (no dependencies):**
1. Unit-1 (Config Core)
2. Unit-3 (Logging)

**Can start after Unit-1:**
1. Unit-7 (Config API)
2. Unit-10 (Data Warehouse)

**Can start after Unit-2 + Unit-1 + Unit-3:**
1. Unit-4 (Auth Core)

**Can start after Unit-4:**
1. Unit-5 (Auth Resilience) - parallel
2. Unit-8 (Auth API) - sequential after Unit-5
3. Unit-6 (Gate Interface) - parallel with Unit-8

**Can start after Unit-4 + Unit-3:**
1. Unit-9 (Monitoring)

**Can start after all others:**
1. Unit-11 (E2E Testing)

---

## Development Timeline

### Critical Path Analysis

**Blocker #1: Processor API Specification**
- Impact: Blocks Unit-2 (3-4 weeks)
- Mitigation: Start Unit-2 with mock processor, swap real processor later
- Action: Get processor spec by **end of March 2026** (today + 2 weeks)
- Fallback: Pre-negotiate processor API contract ASAP

**Blocker #2: Gate Hardware Integration Details**
- Impact: Blocks Unit-6 (affects overall integration timeline)
- Mitigation: Develop against hardware simulator, integration test later
- Action: Get hardware details by **end of April 2026** (6 weeks)
- Fallback: Implement generic hardware interface, mock for dev

### Timeline Chart (Gantt)

```
Week    Task (Weeks 1-22)
1-2     Unit-1 (Config) + Unit-3 (Logging) [parallel]
2-3     Unit-2 (Processor) [depends on API spec]
3-6     Unit-4 (Auth Core) [depends on 1,2,3]
4-6     Unit-7 (Config API) [depends on 1, parallel with 4]
5-7     Unit-5 (Auth Resilience) [depends on 4, parallel]
6-8     Unit-10 (Data Warehouse) [depends on 3]
8-10    Unit-8 (Auth API) [depends on 4,5]
7-9     Unit-6 (Gate Interface) [depends on 4, hardware details]
9-11    Unit-9 (Monitoring) [depends on 3,4]
10-14   (Buffer, testing, hardening)
15-18   Unit-11 (E2E + System Testing)
19-22   (Defect fixes, performance tuning, pilot prep)
```

### Milestone Timeline

| Milestone | Target Week | Target Date | Scope | Go/No-Go |
|-----------|------------|-------------|-------|----------|
| Unit-1,3 Complete | 2 | April 1 | Config + Logging working | Go if latency <100ms |
| Unit-2 Mock Ready | 3 | April 8 | Processor abstraction ready | Go if tests pass |
| Unit-4,5 Complete | 7 | May 6 | Core auth + resilience working | Go if p95 <1500ms |
| Unit-7,8 Complete | 9 | May 20 | APIs working | Go if <50ms response |
| Unit-6 Complete | 10 | May 27 | Gate integration ready | Go if mock tests pass |
| Unit-9,10 Complete | 11 | June 3 | Monitoring + warehouse ready | Go if metrics accurate |
| Unit-11 Complete | 18 | July 22 | E2E tests passing | Go if all tests pass |
| Pilot Ready | 20 | August 5 | Ready for store pilot | Go if no critical bugs |
| Production Ready | 22 | August 19 | Ready for production | Go if compliance verified |

---

## Effort Estimates & Resource Allocation

### By Unit

| Unit | Effort | Person-Weeks | Team | Confidence |
|------|--------|-------------|------|-----------|
| Unit-1 | 2w | 2-3 | 1-2 eng | High |
| Unit-2 | 3-4w | 6-12 | 2-3 eng | Medium (depends on processor) |
| Unit-3 | 2-3w | 2-4 | 1-2 eng | High |
| Unit-4 | 3-4w | 6-12 | 2-3 eng | High |
| Unit-5 | 2-3w | 2-4 | 1-2 eng | High |
| Unit-6 | 2-3w | 2-4 | 1-2 eng | Medium (hardware dependency) |
| Unit-7 | 2-3w | 4-6 | 2 eng | High |
| Unit-8 | 1-2w | 1-2 | 1 eng | High |
| Unit-9 | 2-3w | 2-4 | 1-2 eng | High |
| Unit-10 | 2-3w | 2-4 | 1-2 eng | High |
| Unit-11 | 3-4w | 6-12 | 2-3 eng | High |
| **TOTAL** | **24-32 weeks** | **35-69 person-weeks** | **4-6 eng** | **Medium** |

### Resource Allocation Scenarios

**Option A: Full Team (6 Engineers, 24-26 weeks)**
```
Sprint 1-2 (Weeks 1-2):
  - Team A (2 eng): Unit-1 (Config Core)
  - Team B (2 eng): Unit-3 (Logging)
  - Team C (2 eng): Unit-2 prep (Processor API definition)

Sprint 3-4 (Weeks 3-4):
  - Team C (2 eng): Unit-2 (Processor Integration)
  - Team A (2 eng): Unit-7 (Config API, parallel)
  - Team B (2 eng): Unit-3 finalize + start Unit-10 (Data Warehouse)

Sprint 5-6 (Weeks 5-6):
  - Team D (5 eng): Unit-4 (Auth Core)
  - Team B (1 eng): Unit-10 (continue)

Sprint 7-8 (Weeks 7-8):
  - Team D (3 eng): Unit-5 (Auth Resilience)
  - Team E (2 eng): Unit-6 (Gate Interface)
  - Team B (1 eng): Unit-9 (Monitoring)

Sprint 9-10 (Weeks 9-10):
  - Team D (3 eng): Unit-8 (Auth API)
  - Team E (2 eng): Unit-6 (continue)
  - Team B (1 eng): Unit-9 (continue)

Sprint 11-14 (Weeks 11-14):
  - Buffer: refinement, hardening, defect fixes

Sprint 15-18 (Weeks 15-18):
  - Team F (5 eng): Unit-11 (E2E Testing)
  - Other teams: support, docs

Sprint 19-22 (Weeks 19-22):
  - All teams: Issue resolution, pilot prep
```

**Option B: Lean Team (4 Engineers, 28-32 weeks)**
```
- Parallel execution reduced
- Longer individual phases
- Risk: Critical path delays have bigger impact
- Benefit: Cost reduction
```

### Staffing Recommendations

**Optimal Team Composition (6 Engineers):**
1. **Backend Lead** (1): Oversees Units 4,5,8 (core logic)
2. **Backend Engineers** (2): Unit-4,5 implementation
3. **Integration Lead** (1): Units 2,6,7 (bridges internal/external)
4. **Integration Engineers** (1): Unit-2,6,7 implementation
5. **Data Engineer** (1): Units 3,9,10,11 (logging, monitoring, warehouse, testing)

**Critical Roles:**
- **Unit-2 Lead**: Needs payment processing domain knowledge
- **Unit-4 Lead**: Needs micro-services, resilience pattern experience
- **Unit-11 Lead**: Needs testing, performance optimization experience

---

## Risk Assessment & Mitigations

### Critical Risks

| Risk | Impact | Probability | Mitigation | Owner |
|------|--------|------------|-----------|-------|
| **Processor API changes** | Unit-2 rework (2-3 weeks) | Medium | Get API spec early, maintain loose coupling | Integration Lead |
| **Gate hardware unavailable** | Unit-6 blocked | Medium | Develop mock hardware interface, integration test later | Integration Lead |
| **Latency SLA unmet** | MVP fail (1.5s+) | Medium | Performance test early (Unit-4), profile, optimize | Backend Lead |
| **PCI-DSS compliance gap** | Delayed pilot | Medium | Compliance review at Unit-4, not end | Backend Lead |
| **Concurrent update conflicts** | Data integrity issues | Low | Unit-1 concurrency testing, pessimistic locking | Backend Engineer |
| **Processor timeout rate high** | Circuit breaker trips often | Medium | Test with real processor latency distribution | Integration Engineer |
| **Config propagation lag** | Stale decisions (5 min) | Low | Use defaults, acceptable tradeoff | Integration Lead |

### Medium Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Data warehouse query slow** | Reporting delays | Start with partition strategy, index early |
| **Hardware integration complex** | Unit-6 delay | Get hardware spec early, mock interface |
| **Team lacks payment domain** | Design rework | Hire domain expert early, training |
| **Testing coverage gaps** | Bugs in production | Use TDD, code review, mutation testing |

### Risk Mitigation Strategies

1. **Get Processor API spec by March 31** (non-negotiable)
2. **Weekly architecture review** (Unit-1 → Unit-4 → Unit-11 gates)
3. **Performance testing from day 1** (latency non-negotiable in Phase 1)
4. **Compliance checkpoints** (Unit-4 mid-point, not end)
5. **Integration testing mock-first** (hardware, processor) before real ones
6. **Knowledge sharing sessions** (payment domain, architecture decisions)

---

## Testing Strategy by Unit

### Unit-1: Configuration Service

**Test Coverage Target**: 90%+

**Test Categories**:
- Unit tests (CRUD operations)
- Edge cases (invalid inputs, boundary values)
- Concurrency (simultaneous updates)
- Performance (<50ms retrieval)

**Tools**: JUnit/Pytest, Mockito, load testing

---

### Unit-2: Processor Integration

**Test Coverage Target**: 95%+

**Test Categories**:
- API contract tests (preauth, balance, reverse)
- Error response handling (timeouts, errors, missing data)
- Tokenization (card data masking)
- Timeout enforcement
- Retry logic
- Circuit breaker state transitions

**Tools**: Wiremock (mock processor), JUnit/Pytest, load testing

---

### Unit-3: Logging

**Test Coverage Target**: 90%+

**Test Categories**:
- Event creation (all event types)
- Sensitive data filtering (no card numbers)
- Queue publishing (delivery verification)
- High-volume handling (1000+ events/sec)
- Data warehouse ingestion

**Tools**: JUnit/Pytest, Kafka test containers, warehouse queries

---

### Unit-4: Authorization Service

**Test Coverage Target**: 95%+

**Test Categories**:
- Happy path (all decision scenarios)
- Error paths (8 denial types)
- Latency (p95 <1500ms)
- Concurrency (100+ simultaneous requests)
- State machine (decision logic correctness)

**Tools**: JUnit/Pytest, Testcontainers, load testing, integration tests

---

### Unit-11: E2E Testing

**Test Coverage Target**: 100% of customer flows

**Test Categories**:
- End-to-end (card → approval → gate)
- Error scenarios (timeout, missing balance, etc.)
- Performance (sustained 100+ req/sec)
- Security (tokenization, encryption, injection)
- Load testing (scaling to peak demand)
- Compliance (PCI-DSS validation)

**Tools**: Selenium/Playwright (UI), JMeter/Locust (load), OWASP ZAP (security)

---

## Deployment & Rollout Plan

### Deployment Architecture

**Dev Environment**:
- Local Docker Compose
- Mock processor, gate hardware
- Unit-level testing

**Staging Environment**:
- Kubernetes cluster (similar to prod)
- Real processor (sandbox credentials)
- Mock gate hardware
- Integration testing

**Production Environment**:
- Multi-zone Kubernetes (high availability)
- Real processor (prod credentials)
- Real gate hardware
- Continuous monitoring

### Pilot Plan (1-2 Stores, October 2026)

**Timeline**: 4-6 weeks

**Scope**:
- 2 geographically diverse stores
- Real prepaid customers
- Real processor transactions
- Continuous monitoring

**Success Criteria**:
- Approval rate ≥60% (target: 65%)
- Payment completion ≥80% (target: 85%)
- System uptime >99%
- No customer complaints
- All metrics meet targets

**Rollout Triggers**:
- ✅ Pilot successful (all criteria met) → Full rollout
- ⚠️ Pilot marginal (some criteria missed) → Extended pilot (2-4 weeks)
- ❌ Pilot failed (critical metrics missed) → Engineering deep dive (2-4 weeks)

### Production Rollout (December 2026)

**Timeline**: 2-4 weeks

**Rollout Strategy**: Phased by region
1. **Week 1**: 10% of stores (100-150 stores)
2. **Week 2**: 25% of stores (250-375 stores)
3. **Week 3**: 50% of stores (500-750 stores)
4. **Week 4**: 100% of stores (1000+ stores)

**Rollback Plan**: Instant rollback if:
- Error rate >5%
- Approval rate <50%
- Uptime <99%
- Critical security vulnerability

---

## Summary

**Total Timeline**: 20-22 weeks to production-ready (plus 4-6 week pilot)

**Team Size**: 4-6 engineers

**Key Blockers**:
1. Processor API spec (need by March 31)
2. Gate hardware details (need by April 30)

**Critical Success Factors**:
1. Performance (latency <1.5s) - must test early
2. Processor reliability - choose wisely, test thoroughly
3. Configuration management - get defaults right
4. Compliance - PCI-DSS review mid-way, not end

**Next Steps**:
1. ✅ Get processor API specification (this week)
2. ✅ Get gate hardware integration details (next 6 weeks)
3. ✅ Assign engineering teams to units
4. ✅ Start Unit-1 & Unit-3 (this week)
5. ✅ Weekly architecture review meetings

---

**Document Version**: 1.0  
**Last Updated**: March 16, 2026  
**Status**: Ready for Engineering  
**Next Phase**: Units Generation (detailed spec writing)
