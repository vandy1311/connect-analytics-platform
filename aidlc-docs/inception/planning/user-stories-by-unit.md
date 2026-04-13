# User Stories Mapping - Phase 1 Development Units

**Document**: User Stories by Development Unit  
**Version**: 1.0  
**Date**: March 16, 2026  
**Project**: JWO Prepaid Card Balance Check - Phase 1 MVP  
**Related Document**: [units-planning-phase1.md](units-planning-phase1.md)

---

## Overview

This document maps user stories to each of the 11 development units defined in the Units Planning document. Each story follows the standard format:

```
As a [role], 
I want to [action], 
so that [benefit]

Acceptance Criteria:
  [ ] Criterion 1
  [ ] Criterion 2
  ...
```

**Notation**:
- **Story Points**: Estimated effort (1-13 scale, Fibonacci)
- **Sprint**: Suggested sprint assignment (relative to unit timeline)
- **Priority**: Critical, High, Medium, Low (based on dependencies)
- **Owner**: Recommended team lead

---

## Unit-1: Configuration Service - Core

### Story 1.1: Create Configuration Store Schema

**As a** backend engineer,  
**I want to** design and create the PostgreSQL schema for storing per-store configurations,  
**so that** configurations can be reliably persisted and retrieved.

**Acceptance Criteria**:
- [ ] PostgreSQL table `store_configurations` created with columns: `store_id`, `threshold_multiplier`, `average_basket_size`, `created_at`, `updated_at`
- [ ] `store_id` is unique constraint and primary key
- [ ] `threshold_multiplier` accepts float values 0.5-10.0 with validation
- [ ] `average_basket_size` accepts decimal values > 0 with validation
- [ ] Migration script created and runnable
- [ ] Schema documented with column descriptions
- [ ] Database connection pooling configured

**Story Points**: 3  
**Sprint**: 1  
**Priority**: Critical  
**Owner**: Backend Engineer (DB specialist preferred)

---

### Story 1.2: Implement ConfigRepository CRUD Operations

**As a** backend engineer,  
**I want to** implement the ConfigRepository with Create, Read, Update, Delete operations,  
**so that** configuration data can be accessed programmatically.

**Acceptance Criteria**:
- [ ] ConfigRepository class created with methods: `create()`, `getById()`, `update()`, `delete()`
- [ ] `create()` returns the created configuration
- [ ] `getById()` returns configuration or null
- [ ] `update()` modifies existing configuration
- [ ] `delete()` removes configuration by store_id
- [ ] All methods include transaction handling
- [ ] Repository tests achieve 95%+ coverage
- [ ] No SQL injection vulnerabilities

**Story Points**: 5  
**Sprint**: 1-2  
**Priority**: Critical  
**Owner**: Backend Engineer

---

### Story 1.3: Implement ConfigService with Business Logic

**As a** service layer,  
**I want to** provide ConfigService that wraps repository and handles defaults,  
**so that** missing configurations return sensible defaults instead of nulls.

**Acceptance Criteria**:
- [ ] ConfigService class created with method: `getConfig(store_id)`
- [ ] Returns configuration if found
- [ ] Returns defaults (3x multiplier, $50 basket) if not found
- [ ] Default values configurable via constants
- [ ] Validation logic for threshold_multiplier (0.5-10.0) and basket_size (>0)
- [ ] Throws ValidationException on invalid data
- [ ] Service tests achieve 95%+ coverage
- [ ] In-memory caching configuration (TTL configurable)

**Story Points**: 5  
**Sprint**: 2  
**Priority**: Critical  
**Owner**: Backend Lead

---

### Story 1.4: Add Caching Layer for Configuration Performance

**As a** system engineer,  
**I want to** add local in-memory caching with TTL for configurations,  
**so that** configuration retrieval latency stays under 50ms.

**Acceptance Criteria**:
- [ ] Local cache (e.g., Caffeine, Spring Cache) configured
- [ ] Cache TTL set to 5 minutes (configurable)
- [ ] Cache hit returns <10ms latency
- [ ] Cache miss fetches from DB and updates cache
- [ ] Cache invalidation on config update
- [ ] Cache statistics exposed via metrics
- [ ] Load test confirms <50ms p95 latency
- [ ] Cache size monitoring in place

**Story Points**: 3  
**Sprint**: 2  
**Priority**: High  
**Owner**: Backend Engineer

---

### Story 1.5: Unit Test Coverage for Configuration Service

**As a** QA engineer,  
**I want to** write comprehensive unit tests for configuration operations,  
**so that** configuration logic is thoroughly validated.

**Acceptance Criteria**:
- [ ] Tests for CRUD operations (create, read, update, delete)
- [ ] Tests for default values (missing config returns defaults)
- [ ] Tests for validation (invalid inputs rejected)
- [ ] Tests for concurrency (simultaneous updates handled)
- [ ] Tests for edge cases (empty store_id, boundary values)
- [ ] Test coverage ≥95%
- [ ] All tests passing with no flakes
- [ ] Performance test: 100 sequential reads <5sec

**Story Points**: 5  
**Sprint**: 2  
**Priority**: Critical  
**Owner**: QA Engineer

---

## Unit-2: Payment Processor Integration Layer

### Story 2.1: Define Payment Processor API Abstraction

**As a** integration engineer,  
**I want to** define a PaymentProcessorClient interface that abstracts the processor API,  
**so that** processor implementations can be swapped without changing core logic.

**Acceptance Criteria**:
- [ ] PaymentProcessorClient interface defined with 3 methods: `queryBalance()`, `reversePreauth()`, `lookupBIN()`
- [ ] Method signatures include timeout and error handling
- [ ] BalanceQueryResponse DTO includes: status, available_balance, preauth_id, error
- [ ] PreauthReverseRequest/Response DTOs defined
- [ ] BINLookupResponse includes: card_type, network, is_prepaid
- [ ] All DTOs include validation
- [ ] Interface documentation complete with javadoc
- [ ] Interface tested with mock implementations

**Story Points**: 3  
**Sprint**: 1  
**Priority**: Critical (BLOCKER)  
**Owner**: Integration Architect

**Blocker Note**: Requires processor API specification by March 31, 2026

---

### Story 2.2: Implement Concrete Processor Client

**As a** integration engineer,  
**I want to** implement the concrete PaymentProcessorClient that calls the real processor API,  
**so that** the system can query actual card balances.

**Acceptance Criteria**:
- [ ] ProcessorApiClient class implements PaymentProcessorClient interface
- [ ] queryBalance() method calls processor endpoint with proper request format
- [ ] Request includes: card_token, transaction_amount, store_id
- [ ] Response parsed and mapped to BalanceQueryResponse
- [ ] HTTP status codes mapped to response status (success, error, timeout)
- [ ] TLS 1.2+ enforced on all connections
- [ ] Request/response logging (without sensitive data)
- [ ] Error codes from processor mapped to internal error types
- [ ] Unit tests with mock HTTP responses
- [ ] Integration test with sandbox processor credentials

**Story Points**: 8  
**Sprint**: 3-4  
**Priority**: Critical (BLOCKER)  
**Owner**: Integration Engineer

---

### Story 2.3: Implement Card Tokenization Service

**As a** security engineer,  
**I want to** tokenize card data before sending to processor,  
**so that** full card numbers are never stored or logged.

**Acceptance Criteria**:
- [ ] TokenizationService class created
- [ ] tokenize(cardData) method accepts: card_number, exp_date, cvv
- [ ] Returns: token (processable by processor), card_last_4_hashed
- [ ] Full card_number never stored or logged
- [ ] Tokenization happens before any processor call
- [ ] Detokenization only possible via processor (never internal)
- [ ] Unit tests verify card number is never exposed
- [ ] Integration test with real processor tokenization
- [ ] PCI-DSS documentation updated

**Story Points**: 5  
**Sprint**: 3  
**Priority**: Critical (Security)  
**Owner**: Security Engineer

---

### Story 2.4: Implement BIN Lookup & Prepaid Classification

**As a** integration engineer,  
**I want to** implement BIN lookup to classify cards as prepaid or non-prepaid,  
**so that** only prepaid cards are authorized.

**Acceptance Criteria**:
- [ ] BINLookupService class created
- [ ] lookupBIN(cardNumber) returns: card_type, network, is_prepaid
- [ ] BIN data sourced from processor API
- [ ] Results cached locally with 24-hour expiration
- [ ] Cache hit performs in <20ms
- [ ] Non-prepaid cards return is_prepaid=false
- [ ] Unit tests cover hit/miss scenarios
- [ ] Integration test verifies processor BIN data
- [ ] Test data includes: Visa, Mastercard, Amex, prepaid variants

**Story Points**: 5  
**Sprint**: 3  
**Priority**: High  
**Owner**: Integration Engineer

---

### Story 2.5: Implement Preauth Reversal Service

**As a** integration engineer,  
**I want to** implement reversal of preauthorizations when balance is insufficient,  
**so that** failed transactions don't lock customer funds.

**Acceptance Criteria**:
- [ ] PreauthReversalService class created
- [ ] reversePreauth(preauthId) calls processor reversal endpoint
- [ ] Response includes: status, voided_amount, error (if any)
- [ ] Timeout set to 600ms (fail-safe: no reversal on timeout)
- [ ] Retry logic: single retry on transient error
- [ ] Reversal attempt logged with result
- [ ] Unit tests cover: success, timeout, error, retry scenarios
- [ ] Integration test with processor sandbox
- [ ] SLA: <200ms p95 latency

**Story Points**: 5  
**Sprint**: 4  
**Priority**: High  
**Owner**: Integration Engineer

---

### Story 2.6: Implement Timeout & Retry Logic

**As a** resilience engineer,  
**I want to** add timeout and retry mechanisms to processor calls,  
**so that** transient errors don't cause authorization failures.

**Acceptance Criteria**:
- [ ] TimeoutManager enforces 800ms timeout on all processor calls
- [ ] Timeout exceptions caught and mapped to DENY_TIMEOUT
- [ ] Retry policy: single retry on transient errors (network timeout, 503)
- [ ] No retry on permanent errors (400, 401, 403, 404)
- [ ] Exponential backoff: 100ms + jitter
- [ ] Retry count tracked and logged
- [ ] Unit tests cover: timeout, retry success, retry failure, no-retry scenarios
- [ ] Load test: 100 concurrent requests with timeouts
- [ ] Metrics: timeout_count, retry_count, retry_success_rate

**Story Points**: 5  
**Sprint**: 3  
**Priority**: High  
**Owner**: Resilience Engineer

---

### Story 2.7: Mock Processor for Testing & Development

**As a** developer,  
**I want to** use a mock processor implementation for local testing,  
**so that** development can proceed without a real processor.

**Acceptance Criteria**:
- [ ] MockProcessorClient implements PaymentProcessorClient interface
- [ ] Supports test scenarios: approved, denied, timeout, error
- [ ] queryBalance() returns configurable balances
- [ ] Timeout scenarios tested by adding artificial delay
- [ ] Error scenarios tested with error response
- [ ] BIN lookup returns prepaid=true for test cards
- [ ] Mock behavior configuration via test fixtures
- [ ] Mock processor used in all unit tests
- [ ] Swap to real processor for integration tests

**Story Points**: 3  
**Sprint**: 3  
**Priority**: High  
**Owner**: QA Engineer

---

### Story 2.8: Integration Tests with Processor API

**As a** QA engineer,  
**I want to** test processor integration with sandbox credentials,  
**so that** real processor behavior is validated before production.

**Acceptance Criteria**:
- [ ] Integration test suite created for processor client
- [ ] Tests use sandbox processor credentials (environment variables)
- [ ] Tests cover: happy path, error, timeout, invalid data
- [ ] Sandbox transactions tracked for audit
- [ ] BIN lookup verified with real data
- [ ] Tokenization verified with processor
- [ ] Reversal tested with actual preauth
- [ ] All tests passing consistently
- [ ] Processor latency baseline established
- [ ] Test data usage monitoring in place

**Story Points**: 5  
**Sprint**: 4  
**Priority**: High  
**Owner**: QA Engineer

---

## Unit-3: Logging Service - Event Capture

### Story 3.1: Define Event Models & Schemas

**As a** architect,  
**I want to** define event model classes for all authorization events,  
**so that** events are consistently structured and serializable.

**Acceptance Criteria**:
- [ ] Event base class defined with common fields: event_id, timestamp, request_id
- [ ] AuthorizationAttemptEvent defined with: store_id, card_network, decision, balance_info
- [ ] ApprovalEvent, DenialEvent, ErrorEvent subclasses
- [ ] All events immutable (final fields, no setters)
- [ ] Events serializable to JSON with Jackson
- [ ] Sensitive fields excluded from serialization (@JsonIgnore)
- [ ] Schema documentation with field descriptions
- [ ] Unit tests verify JSON serialization correctness

**Story Points**: 3  
**Sprint**: 1  
**Priority**: High  
**Owner**: Architect

---

### Story 3.2: Implement Event Logger with PCI-DSS Masking

**As a** security engineer,  
**I want to** implement event logger that masks sensitive data before writing,  
**so that** no PCI-DSS violations occur through logging.

**Acceptance Criteria**:
- [ ] EventLogger interface created with method: `log(event)`
- [ ] Masking logic: card_number → NEVER logged, card_last_4_hashed instead
- [ ] Masking logic: card_expiry → NEVER logged
- [ ] Masking logic: CVV → NEVER logged
- [ ] Card_token logged (processor token, not original card)
- [ ] Card_last_4 hashed with SHA256
- [ ] All sensitive fields documented with masking rules
- [ ] Unit tests verify no sensitive data in logs
- [ ] Integration test with real event data
- [ ] PCI-DSS compliance checklist signed off

**Story Points**: 5  
**Sprint**: 1-2  
**Priority**: Critical (Security)  
**Owner**: Security Engineer

---

### Story 3.3: Implement Event Repository for Data Warehouse

**As a** data engineer,  
**I want to** implement EventRepository that writes events to data warehouse,  
**so that** events are persisted for analytics and audit.

**Acceptance Criteria**:
- [ ] EventRepository class created with method: `save(event)`
- [ ] save() serializes event to JSON
- [ ] Event inserted into warehouse table with timestamp
- [ ] Batch insertion supported for performance
- [ ] Connection pooling configured for warehouse
- [ ] Transactions ensure all-or-nothing writes
- [ ] Unit tests with mock warehouse
- [ ] Load test: 1000 events/sec sustained
- [ ] Write latency <100ms p95
- [ ] Backup/recovery tested

**Story Points**: 5  
**Sprint**: 2  
**Priority**: High  
**Owner**: Data Engineer

---

### Story 3.4: Implement Message Queue Producer for Async Processing

**As a** architect,  
**I want to** add event publishing to message queue (Kafka),  
**so that** events are processed asynchronously without blocking authorization.

**Acceptance Criteria**:
- [ ] MessageQueueProducer class created
- [ ] Events published to Kafka topic: `authorization-events`
- [ ] Publish happens async (non-blocking)
- [ ] Publish timeout: 100ms (fail-silent)
- [ ] Message key: store_id (for partitioning)
- [ ] Message value: JSON event
- [ ] Topic configured with 12-hour retention
- [ ] Producer error handling: log and continue
- [ ] Unit tests with embedded Kafka
- [ ] Integration test with real Kafka

**Story Points**: 5  
**Sprint**: 2  
**Priority**: High  
**Owner**: Architect

---

### Story 3.5: Implement Async Event Handler

**As a** service engineer,  
**I want to** implement consumer that processes events from message queue,  
**so that** events are reliably delivered to data warehouse.

**Acceptance Criteria**:
- [ ] EventConsumer class created, consumes from Kafka
- [ ] For each event: save to warehouse, track offset
- [ ] Error handling: log error, retry with exponential backoff
- [ ] Failed messages sent to dead-letter queue after 3 retries
- [ ] Offset committed only after successful save
- [ ] Consumer lag monitored and alerted
- [ ] Unit tests with embedded Kafka
- [ ] Load test: 1000 events/sec throughput
- [ ] Recovery test: consumer restarts don't lose events

**Story Points**: 5  
**Sprint**: 2-3  
**Priority**: High  
**Owner**: Service Engineer

---

### Story 3.6: Unit & Integration Tests for Logging Service

**As a** QA engineer,  
**I want to** comprehensively test the logging service,  
**so that** event capture is reliable and secure.

**Acceptance Criteria**:
- [ ] Unit tests for EventLogger (masking logic)
- [ ] Unit tests for EventRepository (CRUD)
- [ ] Unit tests for MessageQueueProducer
- [ ] Integration tests: end-to-end event flow
- [ ] Security tests: verify no sensitive data leaked
- [ ] Load tests: 1000 events/sec sustained
- [ ] Test coverage ≥95%
- [ ] High-volume event handling verified
- [ ] Data warehouse query validation

**Story Points**: 5  
**Sprint**: 3  
**Priority**: High  
**Owner**: QA Engineer

---

## Unit-4: Authorization Service - Core Logic

### Story 4.1: Implement AuthorizationService Orchestrator

**As a** backend lead,  
**I want to** create AuthorizationService that orchestrates the authorization flow,  
**so that** decision-making is coordinated across multiple services.

**Acceptance Criteria**:
- [ ] AuthorizationService class created with method: `authorize(cardData, storeId)`
- [ ] Method returns: AuthorizationDecision with decision (approved/denied), balance_info, latency_ms
- [ ] Service calls BINLookupService, ConfigService, ProcessorClient in sequence
- [ ] Service catches all exceptions and logs appropriately
- [ ] Decision logged to EventLogger
- [ ] Latency tracked and reported
- [ ] Method timeout: 1200ms max
- [ ] Unit tests with mocked dependencies
- [ ] Integration tests with real service chain

**Story Points**: 8  
**Sprint**: 5  
**Priority**: Critical  
**Owner**: Backend Lead

---

### Story 4.2: Implement DecisionEngine with State Machine Logic

**As a** service architect,  
**I want to** implement DecisionEngine that applies authorization business logic,  
**so that** decision rules are clear and versioned.

**Acceptance Criteria**:
- [ ] DecisionEngine class created with method: `decide(binLookup, config, balance)`
- [ ] Returns: AuthorizationDecision with 8 possible outcomes:
  - APPROVED
  - DENIED_NOT_PREPAID
  - DENIED_INSUFFICIENT_BALANCE
  - DENIED_TIMEOUT
  - DENIED_PROCESSOR_ERROR
  - DENIED_NO_BALANCE
  - DENIED_MISSING_CONFIG
  - DENIED_INVALID_INPUT
- [ ] Decision logic documented with state transition rules
- [ ] All paths covered by unit tests
- [ ] No null pointer exceptions
- [ ] Deterministic (same input → same output)

**Story Points**: 8  
**Sprint**: 5  
**Priority**: Critical  
**Owner**: Service Architect

---

### Story 4.3: Implement Threshold Calculator

**As a** service engineer,  
**I want to** implement ThresholdCalculator that computes required balance,  
**so that** balance comparison is consistent.

**Acceptance Criteria**:
- [ ] ThresholdCalculator class created with method: `calculateRequired(config)`
- [ ] Formula: required = config.multiplier × config.average_basket_size
- [ ] Input validation: multiplier (0.5-10.0), basket_size (>0)
- [ ] Output: required_balance_cents (always positive integer)
- [ ] Handles decimal calculations accurately (no rounding errors)
- [ ] Unit tests cover: normal, boundary, edge cases
- [ ] Performance: <50ms for 1000 calculations
- [ ] No floating-point precision issues

**Story Points**: 3  
**Sprint**: 5  
**Priority**: High  
**Owner**: Service Engineer

---

### Story 4.4: Implement BIN Classifier

**As a** service engineer,  
**I want to** classify card BINs as prepaid or non-prepaid,  
**so that** only prepaid cards are authorized.

**Acceptance Criteria**:
- [ ] BINClassifier class created with method: `isPrepaid(binLookup)`
- [ ] Returns: boolean (true = prepaid, false = non-prepaid)
- [ ] Handles: Visa prepaid, Mastercard prepaid, prepaid-only networks
- [ ] Unit tests with real BIN data
- [ ] Classification accuracy >99% for major networks

**Story Points**: 3  
**Sprint**: 5  
**Priority**: High  
**Owner**: Service Engineer

---

### Story 4.5: Implement Error Handling Matrix

**As a** service engineer,  
**I want to** define error handling rules for different processor errors,  
**so that** errors are handled consistently.

**Acceptance Criteria**:
- [ ] ErrorHandler class created with method: `handle(exception, context)`
- [ ] Returns: AuthorizationDecision with appropriate denial reason
- [ ] Error mapping: TimeoutException → DENIED_TIMEOUT
- [ ] Error mapping: ProcessorException → DENIED_PROCESSOR_ERROR
- [ ] Error mapping: ValidationException → DENIED_INVALID_INPUT
- [ ] All errors logged with full context
- [ ] Error tracking metrics exposed
- [ ] Unit tests cover all error types

**Story Points**: 5  
**Sprint**: 5  
**Priority**: High  
**Owner**: Service Engineer

---

### Story 4.6: Implement Circuit Breaker for Processor Calls

**As a** resilience engineer,  
**I want to** add circuit breaker pattern to processor calls,  
**so that** cascading failures are prevented.

**Acceptance Criteria**:
- [ ] CircuitBreaker state machine: CLOSED → OPEN → HALF_OPEN → CLOSED
- [ ] CLOSED: Forward requests normally
- [ ] OPEN: Fail-fast with DENIED_TIMEOUT (after 50%+ errors in 1 minute)
- [ ] HALF_OPEN: Allow single test request
- [ ] Metrics: circuit breaker state, open count, recovery time
- [ ] Unit tests for all state transitions
- [ ] Integration test with real processor error injection

**Story Points**: 5  
**Sprint**: 6  
**Priority**: High  
**Owner**: Resilience Engineer

---

### Story 4.7: Implement Preauth Initiation on Denial

**As a** service engineer,  
**I want to** initiate preauth reversal when balance is insufficient,  
**so that** customer funds aren't locked unnecessarily.

**Acceptance Criteria**:
- [ ] AuthorizationService monitors decision
- [ ] If decision = DENIED_INSUFFICIENT_BALANCE, initiate reversal
- [ ] Reversal happens asynchronously (don't block response)
- [ ] Reversal result logged separately
- [ ] Failed reversals alerted to ops
- [ ] Unit tests: reversal initiated in right scenarios
- [ ] Integration test: actual reversal with processor

**Story Points**: 5  
**Sprint**: 6  
**Priority**: High  
**Owner**: Service Engineer

---

### Story 4.8: Comprehensive Unit Tests for Authorization Core

**As a** QA engineer,  
**I want to** test the authorization service thoroughly,  
**so that** decision logic is validated across all scenarios.

**Acceptance Criteria**:
- [ ] Test all 8 decision outcomes (approved + 7 denial types)
- [ ] Test happy path: prepaid card → sufficient balance → approved
- [ ] Test error paths: not prepaid, insufficient balance, timeout, errors
- [ ] Test config defaults: missing config returns defaults
- [ ] Test latency: p95 <1500ms
- [ ] Test concurrency: 10 simultaneous requests handled correctly
- [ ] Test coverage ≥95%
- [ ] All tests pass consistently (no flakes)
- [ ] Performance test baseline established

**Story Points**: 8  
**Sprint**: 6-7  
**Priority**: Critical  
**Owner**: QA Engineer

---

## Unit-5: Authorization Service - Resilience & Monitoring

### Story 5.1: Implement Metrics Collection

**As a** monitoring engineer,  
**I want to** collect metrics on authorization service performance,  
**so that** operational health is visible.

**Acceptance Criteria**:
- [ ] MetricsCollector class created
- [ ] Metrics tracked: latency (p50, p95, p99), decision breakdown, error rate
- [ ] Metrics exposed via Micrometer (Prometheus-compatible)
- [ ] Latency metrics: decision phase latency (BIN, config, balance, decision)
- [ ] Decision metrics: approval rate, denial breakdown by type
- [ ] Error metrics: processor errors, timeouts, other errors
- [ ] Metrics update at decision time (minimal overhead <10ms)
- [ ] Integration with monitoring stack (Prometheus, Grafana)

**Story Points**: 5  
**Sprint**: 5  
**Priority**: High  
**Owner**: Monitoring Engineer

---

### Story 5.2: Implement Health Check Endpoint

**As a** operations engineer,  
**I want to** provide a health check endpoint for monitoring,  
**so that** system health is queryable.

**Acceptance Criteria**:
- [ ] GET /health endpoint created
- [ ] Returns: {status: "UP"|"DOWN", components: {...}, timestamp}
- [ ] Component checks: database, processor, config service, message queue
- [ ] Each component: status, latency_ms, last_error (if any)
- [ ] Endpoint responds <100ms (p95)
- [ ] Returns HTTP 200 if UP, 503 if DOWN
- [ ] Health check scheduled every 30 seconds
- [ ] Failed health checks alerted

**Story Points**: 3  
**Sprint**: 6  
**Priority**: High  
**Owner**: Operations Engineer

---

### Story 5.3: Implement Retry Policy for Transient Errors

**As a** resilience engineer,  
**I want to** implement retry logic for transient processor errors,  
**so that** temporary failures don't cause denials.

**Acceptance Criteria**:
- [ ] RetryPolicy class created with method: `execute(callable)`
- [ ] Retry on transient errors: network timeout, 503, 504
- [ ] No retry on permanent errors: 400, 401, 403, 404
- [ ] Retry count: 1 (single retry)
- [ ] Backoff: exponential 100ms + jitter
- [ ] Retry latency adds <200ms on average
- [ ] Unit tests: success on retry, failure after retries, no-retry scenarios
- [ ] Metrics: retry_count, retry_success_rate

**Story Points**: 5  
**Sprint**: 6  
**Priority**: High  
**Owner**: Resilience Engineer

---

### Story 5.4: Implement Error Trend Detection

**As a** monitoring engineer,  
**I want to** detect error trends (e.g., sustained high error rate),  
**so that** operational issues are surfaced proactively.

**Acceptance Criteria**:
- [ ] ErrorTrendDetector class created
- [ ] Tracks error rate over 1-minute window
- [ ] Alert if error rate >5% for >2 consecutive minutes
- [ ] Alert includes: current rate, trend direction, affected service
- [ ] Metrics: error_trend_alerts triggered
- [ ] Unit tests: alert triggering scenarios
- [ ] Integration test with real error injection

**Story Points**: 5  
**Sprint**: 7  
**Priority**: Medium  
**Owner**: Monitoring Engineer

---

### Story 5.5: Implement Timeout Enforcement on All External Calls

**As a** resilience engineer,  
**I want to** enforce strict timeouts on all external service calls,  
**so that** slow responses don't block authorization.

**Acceptance Criteria**:
- [ ] TimeoutManager enforces timeout on:
  - BIN lookup: 200ms
  - Config retrieval: 100ms (cached)
  - Balance query: 600ms
  - Reversal: 200ms
- [ ] Timeout throws TimeoutException
- [ ] TimeoutException caught and mapped to DENIED_TIMEOUT
- [ ] Timeout metrics tracked
- [ ] Unit tests: timeout < configured value
- [ ] Load test: timeouts under load

**Story Points**: 3  
**Sprint**: 6  
**Priority**: High  
**Owner**: Resilience Engineer

---

### Story 5.6: Unit & Integration Tests for Resilience

**As a** QA engineer,  
**I want to** test resilience features comprehensively,  
**so that** fault-tolerance is validated.

**Acceptance Criteria**:
- [ ] Test circuit breaker state transitions
- [ ] Test retry logic success/failure scenarios
- [ ] Test timeout enforcement
- [ ] Test error trend detection
- [ ] Test metrics collection accuracy
- [ ] Test health check endpoint
- [ ] Test high-error-rate scenarios
- [ ] Load test: 100+ concurrent requests with failures
- [ ] Chaos testing: random failures injected

**Story Points**: 8  
**Sprint**: 7  
**Priority**: High  
**Owner**: QA Engineer

---

## Unit-6: Entry Gate Interface - Adapter

### Story 6.1: Define Hardware Adapter Interfaces

**As a** integration architect,  
**I want to** define interfaces for hardware adapters (card reader, display, gate),  
**so that** hardware implementations can be plugged in.

**Acceptance Criteria**:
- [ ] HardwareAdapter interface defined with 3 sub-interfaces:
  - CardReaderAdapter: `onCardRead(cardData) → CardData`
  - DisplayAdapter: `show(message) → void`
  - GateControllerAdapter: `openGate(), closeGate() → void`
- [ ] CardData DTO includes: card_number, card_network, card_last_4
- [ ] Message DTO includes: text, color, duration_ms
- [ ] All interfaces documented with javadoc
- [ ] Mock implementations provided for testing

**Story Points**: 3  
**Sprint**: 3  
**Priority**: Critical  
**Owner**: Integration Architect

**Blocker Note**: Requires hardware integration details (GPIO? REST? Proprietary?)

---

### Story 6.2: Implement Card Data Normalizer

**As a** integration engineer,  
**I want to** normalize card data from hardware into standard format,  
**so that** different card readers produce consistent data.

**Acceptance Criteria**:
- [ ] CardDataNormalizer class created
- [ ] normalize(hardwareCardData) extracts: card_number, network, last_4
- [ ] Handles different input formats (mag stripe, chip, contactless)
- [ ] Validates card_number format (13-19 digits)
- [ ] Handles errors: invalid data → exception + log
- [ ] Unit tests: various input formats
- [ ] Returns consistent CardData DTO

**Story Points**: 3  
**Sprint**: 7  
**Priority**: High  
**Owner**: Integration Engineer

---

### Story 6.3: Implement Request/Response Mapping

**As a** integration engineer,  
**I want to** map hardware events to authorization requests,  
**so that** gate hardware interfaces with authorization service.

**Acceptance Criteria**:
- [ ] EventMapper class created
- [ ] onCardRead(cardData) → AuthorizationRequest
- [ ] AuthorizationRequest includes: card_data, store_id, request_id
- [ ] onAuthorizationResponse(decision) → GateCommand
- [ ] AuthorizationResponse mapping: approved → openGate, denied → closeGate
- [ ] Unit tests: request/response mapping correctness
- [ ] Integration test: actual hardware event flow

**Story Points**: 3  
**Sprint**: 8  
**Priority**: High  
**Owner**: Integration Engineer

---

### Story 6.4: Implement Display Message Templates

**As a** integration engineer,  
**I want to** define display messages for different authorization outcomes,  
**so that** customers see appropriate feedback.

**Acceptance Criteria**:
- [ ] MessageTemplates class created with templates for:
  - APPROVED: "Welcome! Gate opening..." (green, 2 sec)
  - DENIED_INSUFFICIENT: "Insufficient balance. Entry denied." (red, 3 sec)
  - DENIED_NOT_PREPAID: "Prepaid card required. Entry denied." (red, 3 sec)
  - DENIED_TIMEOUT: "System busy. Please try again." (yellow, 3 sec)
- [ ] Templates customizable by store
- [ ] Message rendering tested on display hardware
- [ ] Unit tests: message formatting

**Story Points**: 2  
**Sprint**: 8  
**Priority**: Medium  
**Owner**: Integration Engineer

---

### Story 6.5: Implement Gate Command Executor

**As a** integration engineer,  
**I want to** execute gate control commands (open, close) on hardware,  
**so that** authorized customers can enter.

**Acceptance Criteria**:
- [ ] GateCommandExecutor class created
- [ ] openGate() sends signal to gate hardware
- [ ] closeGate() sends signal to gate hardware
- [ ] Timeout: 2 seconds (gate movement)
- [ ] Error handling: hardware failure → log and close gate
- [ ] Sensor feedback: verify gate opened/closed
- [ ] Unit tests with mock hardware
- [ ] Integration test with actual gate

**Story Points**: 3  
**Sprint**: 8  
**Priority**: High  
**Owner**: Integration Engineer

---

### Story 6.6: Implement Offline Resilience

**As a** operations engineer,  
**I want to** handle offline scenarios (no network),  
**so that** gate can operate in degraded mode.

**Acceptance Criteria**:
- [ ] OfflineModeHandler detects network unavailability
- [ ] Cache last working config + processor response
- [ ] On network loss: use cached config, fail-closed (gate stays closed)
- [ ] On network recovery: sync with server
- [ ] Alert ops on persistent offline state (>5 min)
- [ ] Unit tests: offline detection, failsafe behavior
- [ ] Integration test: network disconnect/reconnect

**Story Points**: 5  
**Sprint**: 8  
**Priority**: Medium  
**Owner**: Operations Engineer

---

### Story 6.7: Implement Hardware Simulator for Development

**As a** developer,  
**I want to** simulate hardware events locally for testing,  
**so that** development doesn't require physical hardware.

**Acceptance Criteria**:
- [ ] HardwareSimulator class created
- [ ] Simulates card reader events (test card numbers)
- [ ] Simulates display (prints to console or test UI)
- [ ] Simulates gate (tracks open/close state)
- [ ] Configurable delays matching real hardware latencies
- [ ] Used in all unit tests
- [ ] Integration test uses simulator then real hardware
- [ ] Test data includes: Visa, Mastercard, prepaid variants

**Story Points**: 3  
**Sprint**: 7  
**Priority**: High  
**Owner**: QA Engineer

---

### Story 6.8: Integration Tests for Gate Interface

**As a** QA engineer,  
**I want to** test gate interface end-to-end,  
**so that** hardware integration is validated.

**Acceptance Criteria**:
- [ ] Test happy path: card → approval → gate opens
- [ ] Test denial path: card → denial → gate stays closed
- [ ] Test display message rendering
- [ ] Test offline handling
- [ ] Test hardware simulator
- [ ] Test with actual hardware (if available)
- [ ] Test coverage ≥90%
- [ ] All tests pass consistently

**Story Points**: 5  
**Sprint**: 9  
**Priority**: High  
**Owner**: QA Engineer

---

## Unit-7: Configuration Service - API & Propagation

### Story 7.1: Implement REST API Endpoints for Config Management

**As a** backend engineer,  
**I want to** expose configuration via REST API,  
**so that** operations can manage store configurations.

**Acceptance Criteria**:
- [ ] GET /config/store/{store_id} endpoint returns current config
- [ ] POST /config/store/{store_id} creates new config
- [ ] PUT /config/store/{store_id} updates existing config
- [ ] All endpoints validate inputs (multiplier, basket_size)
- [ ] Proper HTTP status codes returned (200, 201, 400, 404, 500)
- [ ] API responses include timestamps and version info
- [ ] Swagger/OpenAPI documentation generated
- [ ] Unit tests for all endpoints

**Story Points**: 5  
**Sprint**: 4  
**Priority**: High  
**Owner**: Backend Engineer

---

### Story 7.2: Implement Configuration Change Event Publishing

**As a** architect,  
**I want to** publish configuration changes to event stream,  
**so that** subscribers are notified of updates.

**Acceptance Criteria**:
- [ ] ConfigChangePublisher publishes to Kafka topic: `config-updates`
- [ ] Event includes: store_id, old_config, new_config, timestamp, changed_by
- [ ] Event published synchronously with config update
- [ ] Message key: store_id (for partitioning)
- [ ] Topic retention: 30 days
- [ ] Unit tests with embedded Kafka
- [ ] Integration test with real Kafka

**Story Points**: 3  
**Sprint**: 5  
**Priority**: High  
**Owner**: Architect

---

### Story 7.3: Implement Distributed Cache with Redis

**As a** architect,  
**I want to** add distributed caching for configurations,  
**so that** config retrieval is fast across instances.

**Acceptance Criteria**:
- [ ] DistributedCache class created (Redis-backed)
- [ ] Cache key: `config:{store_id}`
- [ ] Cache value: serialized config JSON
- [ ] Cache TTL: 5 minutes
- [ ] Cache hit latency: <5ms
- [ ] Cache miss fetches from DB and updates cache
- [ ] Cache invalidation on config update
- [ ] Integration with Redis cluster (if using)
- [ ] Fallback to DB on cache unavailability

**Story Points**: 5  
**Sprint**: 5  
**Priority**: Medium  
**Owner**: Architect

---

### Story 7.4: Implement Cache Invalidation on Update

**As a** backend engineer,  
**I want to** invalidate cached configs when they change,  
**so that** stale data isn't served.

**Acceptance Criteria**:
- [ ] CacheInvalidator watches config updates
- [ ] Invalidates cached config on POST/PUT
- [ ] All cache instances invalidated synchronously
- [ ] Invalidation confirmed before returning response
- [ ] Unit tests: invalidation triggers on update
- [ ] Integration test: cache hit after update misses

**Story Points**: 3  
**Sprint**: 5  
**Priority**: High  
**Owner**: Backend Engineer

---

### Story 7.5: Implement Change Validator & Audit Logging

**As a** operations engineer,  
**I want to** validate config changes and audit who made them,  
**so that** unauthorized changes are prevented.

**Acceptance Criteria**:
- [ ] ChangeValidator validates threshold_multiplier (0.5-10.0), basket_size (>0)
- [ ] Rejects changes that fail validation with 400 error
- [ ] AuditLogger tracks: who, when, old_value, new_value
- [ ] Audit log persisted to database
- [ ] Audit log queryable for compliance
- [ ] API endpoint for retrieving audit history
- [ ] Unit tests: validation, audit logging

**Story Points**: 3  
**Sprint**: 5  
**Priority**: High  
**Owner**: Operations Engineer

---

### Story 7.6: Implement Config Subscriber in Authorization Service

**As a** service engineer,  
**I want to** subscribe to config updates from Kafka,  
**so that** authorization service uses latest configs.

**Acceptance Criteria**:
- [ ] ConfigChangeConsumer created, consumes from `config-updates` topic
- [ ] On change event: update local cache
- [ ] On cache update: log change event (for debugging)
- [ ] Failed updates logged with error context
- [ ] Consumer lag monitored and alerted
- [ ] Unit tests with embedded Kafka
- [ ] Integration test: config change propagates to auth service

**Story Points**: 3  
**Sprint**: 6  
**Priority**: High  
**Owner**: Service Engineer

---

### Story 7.7: API Tests for Configuration Endpoints

**As a** QA engineer,  
**I want to** test configuration API comprehensively,  
**so that** API reliability is validated.

**Acceptance Criteria**:
- [ ] Test GET returns current config
- [ ] Test POST creates new config
- [ ] Test PUT updates existing config
- [ ] Test validation rejects invalid data
- [ ] Test concurrent updates (last write wins)
- [ ] Test API response times (<50ms)
- [ ] Test error scenarios (not found, bad request)
- [ ] Load test: 100 concurrent requests
- [ ] Test coverage ≥95%

**Story Points**: 5  
**Sprint**: 6  
**Priority**: High  
**Owner**: QA Engineer

---

## Unit-8: Authorization Service - REST API

### Story 8.1: Implement Authorization REST Endpoint

**As a** backend engineer,  
**I want to** create REST endpoint for authorization checks,  
**so that** gate hardware can request authorization decisions.

**Acceptance Criteria**:
- [ ] POST /authorize/check-entry endpoint created
- [ ] Accepts request: {store_id, card_data, request_id}
- [ ] Returns response: {decision, balance_info, latency_ms}
- [ ] HTTP 200: Decision made (check decision field)
- [ ] HTTP 400: Bad request (invalid input)
- [ ] HTTP 408: Timeout
- [ ] HTTP 503: Service unavailable
- [ ] Request validation: store_id non-empty, card_data complete
- [ ] Response includes decision reason and balance details

**Story Points**: 5  
**Sprint**: 8  
**Priority**: Critical  
**Owner**: Backend Engineer

---

### Story 8.2: Implement Request Validation

**As a** backend engineer,  
**I want to** validate authorization requests,  
**so that** invalid data is rejected early.

**Acceptance Criteria**:
- [ ] RequestValidator validates: store_id (non-empty), card_data (complete)
- [ ] Rejects missing required fields with 400 error
- [ ] Rejects malformed card_data with 400 error
- [ ] Request tracing: request_id tracked through response
- [ ] Unit tests: valid/invalid request scenarios
- [ ] Error messages clear and actionable

**Story Points**: 2  
**Sprint**: 8  
**Priority**: High  
**Owner**: Backend Engineer

---

### Story 8.3: Implement Response Formatting

**As a** backend engineer,  
**I want to** format authorization responses consistently,  
**so that** gate hardware can parse responses reliably.

**Acceptance Criteria**:
- [ ] AuthorizationResponse DTO created with fields:
  - decision (APPROVED|DENIED_*)
  - available_balance_cents (integer)
  - required_balance_cents (integer)
  - total_decision_time_ms (integer)
  - reason (human-readable)
- [ ] Response serialized to JSON
- [ ] Response includes ISO 8601 timestamp
- [ ] Unit tests: JSON serialization correctness
- [ ] Integration test: response matches spec

**Story Points**: 2  
**Sprint**: 8  
**Priority**: High  
**Owner**: Backend Engineer

---

### Story 8.4: REST API Error Handling

**As a** backend engineer,  
**I want to** handle API errors gracefully,  
**so that** clients get helpful error messages.

**Acceptance Criteria**:
- [ ] All exceptions caught and mapped to HTTP responses
- [ ] Error response includes: error_code, message, timestamp
- [ ] 400: Bad request (validation error)
- [ ] 408: Timeout (authorization took >1200ms)
- [ ] 503: Service unavailable (circuit breaker open, DB down)
- [ ] Error messages don't leak sensitive info
- [ ] Unit tests: all error scenarios
- [ ] Integration test: error responses match spec

**Story Points**: 3  
**Sprint**: 8  
**Priority**: High  
**Owner**: Backend Engineer

---

### Story 8.5: REST API Tests

**As a** QA engineer,  
**I want to** comprehensively test the authorization REST endpoint,  
**so that** API reliability is validated.

**Acceptance Criteria**:
- [ ] Test valid request → 200 with decision
- [ ] Test invalid input → 400 error
- [ ] Test timeout → 408 error
- [ ] Test service unavailable → 503 error
- [ ] Test response format correctness
- [ ] Test request tracing (request_id in response)
- [ ] Test concurrent requests
- [ ] Load test: 100+ req/sec
- [ ] Test coverage ≥95%

**Story Points**: 5  
**Sprint**: 9  
**Priority**: High  
**Owner**: QA Engineer

---

## Unit-9: Monitoring & Real-Time Dashboard

### Story 9.1: Implement Metrics Aggregation Service

**As a** monitoring engineer,  
**I want to** aggregate authorization metrics into 5-minute windows,  
**so that** real-time dashboard has current data.

**Acceptance Criteria**:
- [ ] MetricsAggregator consumes metrics from Prometheus/Micrometer
- [ ] Aggregates: count, approval_rate, latency (p50/p95/p99), error_rate
- [ ] 5-minute sliding window
- [ ] Per-store metrics aggregated separately
- [ ] Results stored in time-series DB (InfluxDB, etc.)
- [ ] Query latency <100ms
- [ ] Unit tests: aggregation correctness
- [ ] Integration test: real metrics flow

**Story Points**: 5  
**Sprint**: 9  
**Priority**: High  
**Owner**: Monitoring Engineer

---

### Story 9.2: Implement Dashboard Backend API

**As a** backend engineer,  
**I want to** expose dashboard data via REST API,  
**so that** frontend can render real-time metrics.

**Acceptance Criteria**:
- [ ] GET /dashboard/metrics returns current metrics:
  - Total transactions (5-min window)
  - Approval rate (%)
  - Denial breakdown by type
  - Latency (p50, p95, p99)
  - Error rate (%)
- [ ] GET /dashboard/store/{store_id}/metrics returns per-store metrics
- [ ] Response includes: timestamp, values, trend (↑↓)
- [ ] API response <100ms
- [ ] Endpoint secured (ops/admin only)
- [ ] Unit tests: endpoint correctness

**Story Points**: 3  
**Sprint**: 9  
**Priority**: High  
**Owner**: Backend Engineer

---

### Story 9.3: Implement Alert Rule Engine

**As a** monitoring engineer,  
**I want to** define and execute alert rules,  
**so that** operational issues trigger notifications.

**Acceptance Criteria**:
- [ ] AlertRuleEngine evaluates rules against metrics
- [ ] Rules supported:
  - High latency (p95 > 1500ms for 5 min)
  - High error rate (>5% for 5 min)
  - Processor unavailable (circuit breaker open)
  - Missing config (detected in logs)
- [ ] Alert actions: email, Slack, SMS (configurable)
- [ ] Deduplicate alerts (don't spam on same issue)
- [ ] Unit tests: rule evaluation
- [ ] Integration test: real alert triggering

**Story Points**: 5  
**Sprint**: 10  
**Priority**: High  
**Owner**: Monitoring Engineer

---

### Story 9.4: Implement Trend Analysis

**As a** monitoring engineer,  
**I want to** detect trends in metrics (e.g., growing error rate),  
**so that** issues are surfaced early.

**Acceptance Criteria**:
- [ ] TrendAnalyzer tracks metric changes over time
- [ ] Detects: increasing error rate, decreasing approval rate, rising latency
- [ ] Trend confidence: only alert on statistically significant trends
- [ ] Example: "Approval rate down 5% in last 2 hours"
- [ ] Unit tests: trend detection accuracy
- [ ] Integration test: real trend scenarios

**Story Points**: 5  
**Sprint**: 10  
**Priority**: Medium  
**Owner**: Monitoring Engineer

---

### Story 9.5: Dashboard UI Implementation

**As a** frontend engineer,  
**I want to** build a dashboard UI displaying real-time metrics,  
**so that** operations team can monitor system health.

**Acceptance Criteria**:
- [ ] Dashboard displays:
  - System health (UP/DOWN indicator)
  - Real-time transactions (5-min window)
  - Approval rate (gauge chart)
  - Latency trend (line chart)
  - Error rate (gauge chart)
  - Alert list (most recent)
- [ ] Auto-refresh every 10 seconds
- [ ] Responsive design (desktop/tablet)
- [ ] Color-coded status (green/yellow/red)
- [ ] Per-store drill-down available
- [ ] UI tests: rendering correctness

**Story Points**: 5  
**Sprint**: 10  
**Priority**: Medium  
**Owner**: Frontend Engineer

---

### Story 9.6: Monitoring Integration Tests

**As a** QA engineer,  
**I want to** test monitoring end-to-end,  
**so that** metrics and alerts work correctly.

**Acceptance Criteria**:
- [ ] Test metrics aggregation accuracy
- [ ] Test dashboard API data freshness
- [ ] Test alert rule triggering
- [ ] Test alert deduplicated
- [ ] Test trend detection accuracy
- [ ] Test high-volume metrics (1000+ events/sec)
- [ ] Test coverage ≥90%
- [ ] Load test: 1000+ metrics/sec

**Story Points**: 5  
**Sprint**: 10  
**Priority**: High  
**Owner**: QA Engineer

---

## Unit-10: Data Warehouse & Analytics

### Story 10.1: Design Data Warehouse Schema

**As a** data architect,  
**I want to** design schema for authorization events,  
**so that** analytics queries are efficient.

**Acceptance Criteria**:
- [ ] Table `entry_attempts` designed with columns:
  - event_id (primary key)
  - timestamp (partition key)
  - store_id (index)
  - decision (index)
  - available_balance_cents
  - required_balance_cents
  - decision_time_ms
  - request_id (unique)
- [ ] Partitioning: by date (YYYY-MM-DD)
- [ ] Indexes on: store_id, timestamp, decision
- [ ] Aggregate tables for fast queries
- [ ] Documentation with column descriptions

**Story Points**: 3  
**Sprint**: 2  
**Priority**: High  
**Owner**: Data Architect

---

### Story 10.2: Implement Event Ingestion Pipeline

**As a** data engineer,  
**I want to** build ETL pipeline that ingests events from Kafka,  
**so that** events populate the data warehouse.

**Acceptance Criteria**:
- [ ] DataWarehouseConsumer consumes from `authorization-events` topic
- [ ] Transforms JSON events to warehouse table rows
- [ ] Inserts rows into `entry_attempts` table
- [ ] Batch insertion for performance (500-row batches)
- [ ] Duplicate detection: skip if event_id already exists
- [ ] Data validation: required fields present
- [ ] Error handling: failed rows logged, not lost
- [ ] Latency: <5 min from event to warehouse
- [ ] Unit tests with embedded Kafka
- [ ] Integration test with real warehouse

**Story Points**: 5  
**Sprint**: 3-4  
**Priority**: High  
**Owner**: Data Engineer

---

### Story 10.3: Implement Query Templates for Analytics

**As a** data analyst,  
**I want to** define query templates for common analytics questions,  
**so that** analysis is self-service.

**Acceptance Criteria**:
- [ ] Template: Approval rate by store (daily)
- [ ] Template: Denial breakdown by reason (daily)
- [ ] Template: Latency percentiles (hourly)
- [ ] Template: High-error-rate detection
- [ ] All queries parameterized (date range, etc.)
- [ ] Query execution time <5 seconds
- [ ] Results exportable to CSV
- [ ] Unit tests: query correctness on sample data

**Story Points**: 3  
**Sprint**: 5  
**Priority**: High  
**Owner**: Data Analyst

---

### Story 10.4: Implement Data Retention & Compliance Policy

**As a** compliance engineer,  
**I want to** enforce 2-year data retention with automatic deletion,  
**so that** compliance obligations are met.

**Acceptance Criteria**:
- [ ] Retention policy: keep data for 2 years (730 days)
- [ ] Automatic deletion of data older than 2 years
- [ ] Deletion scheduled daily (batch job)
- [ ] Audit log of deleted data
- [ ] Deletion verification: count of deleted rows tracked
- [ ] PCI-DSS compliance: never delete before 2 years
- [ ] Unit tests: retention logic
- [ ] Integration test: actual deletion with sample data

**Story Points**: 3  
**Sprint**: 5  
**Priority**: High  
**Owner**: Compliance Engineer

---

### Story 10.5: Data Warehouse Integration Tests

**As a** QA engineer,  
**I want to** test data warehouse end-to-end,  
**so that** data integrity is verified.

**Acceptance Criteria**:
- [ ] Test event ingestion accuracy
- [ ] Test data partitioning
- [ ] Test query templates
- [ ] Test retention policy
- [ ] Test duplicate detection
- [ ] Test high-volume ingestion (1000+ events/sec)
- [ ] Test data consistency across replicas
- [ ] Test recovery from failure
- [ ] Test coverage ≥90%

**Story Points**: 5  
**Sprint**: 5-6  
**Priority**: High  
**Owner**: QA Engineer

---

## Unit-11: End-to-End Integration & System Testing

### Story 11.1: Build E2E Test Harness

**As a** QA engineer,  
**I want to** create test harness that simulates complete customer journey,  
**so that** end-to-end behavior is validated.

**Acceptance Criteria**:
- [ ] Test harness simulates: card read → authorization → gate open
- [ ] Harness uses mock hardware by default
- [ ] Harness can switch to real hardware (flag-based)
- [ ] Test data: 50+ test cards (approval, denial, error scenarios)
- [ ] Harness tracks: latency, errors, outcomes
- [ ] Harness integrated with CI/CD pipeline
- [ ] Unit tests: harness correctness

**Story Points**: 5  
**Sprint**: 15  
**Priority**: High  
**Owner**: QA Engineer Lead

---

### Story 11.2: Implement E2E Test Scenarios

**As a** QA engineer,  
**I want to** write comprehensive E2E test scenarios,  
**so that** customer flows are validated.

**Acceptance Criteria**:
- [ ] Happy path: prepaid card → sufficient balance → gate opens
- [ ] Denial paths (7 scenarios):
  - Not prepaid card: gate closes
  - Insufficient balance: reversal initiated, gate closes
  - Processor timeout: deny with timeout reason
  - Processor error: deny with error reason
  - Missing balance: deny
  - Missing config: use defaults, may approve/deny
  - Invalid input: gate closes
- [ ] All paths logged and auditable
- [ ] Test coverage: 100% of decision paths
- [ ] All tests passing consistently

**Story Points**: 8  
**Sprint**: 15-16  
**Priority**: Critical  
**Owner**: QA Engineer

---

### Story 11.3: Performance Testing & Baseline Establishment

**As a** performance engineer,  
**I want to** test system performance under load,  
**so that** SLA targets are verified.

**Acceptance Criteria**:
- [ ] Load test: 100+ decisions/second sustained
- [ ] Latency baseline: p95 <1500ms, p99 <2000ms
- [ ] Approval rate: 60-70% (realistic proportion)
- [ ] Error rate: <1% (timeouts, processor errors)
- [ ] System availability: >99% during test
- [ ] Ramp-up test: latency under increasing load
- [ ] Sustained load test: 1-hour run at peak load
- [ ] Spike test: 3x normal load for 10 minutes
- [ ] Results documented with recommendations

**Story Points**: 8  
**Sprint**: 16-17  
**Priority**: Critical  
**Owner**: Performance Engineer

---

### Story 11.4: Security Testing & Vulnerability Scanning

**As a** security engineer,  
**I want to** test system security comprehensively,  
**so that** vulnerabilities are found and fixed.

**Acceptance Criteria**:
- [ ] OWASP Top 10 testing: all 10 categories tested
- [ ] Injection testing: SQL, command injection
- [ ] Tokenization testing: card number never exposed
- [ ] Encryption testing: TLS 1.2+ verified
- [ ] Access control: RBAC tested
- [ ] Input validation: boundary testing
- [ ] Automated security scanning: OWASP ZAP, Snyk
- [ ] Penetration testing (recommend external expert)
- [ ] No high-severity vulnerabilities found

**Story Points**: 8  
**Sprint**: 17  
**Priority**: Critical  
**Owner**: Security Engineer

---

### Story 11.5: Compliance Validation & Audit

**As a** compliance engineer,  
**I want to** validate system compliance with PCI-DSS,  
**so that** regulatory requirements are met.

**Acceptance Criteria**:
- [ ] PCI-DSS compliance checklist completed
- [ ] Card data never stored in cleartext ✓
- [ ] Tokenization working per spec ✓
- [ ] Encryption in transit (TLS 1.2+) ✓
- [ ] Access control (RBAC) working ✓
- [ ] Logging without sensitive data ✓
- [ ] Data retention (2-year policy) working ✓
- [ ] Audit trails created and queryable ✓
- [ ] Compliance sign-off obtained

**Story Points**: 5  
**Sprint**: 18  
**Priority**: Critical  
**Owner**: Compliance Officer

---

### Story 11.6: Integration Tests - All Components

**As a** QA engineer,  
**I want to** test all components integrated together,  
**so that** system-level behavior is validated.

**Acceptance Criteria**:
- [ ] Config Service: configurations retrieved and used
- [ ] Processor Integration: balance queries work
- [ ] Authorization Service: decisions made correctly
- [ ] Logging Service: events logged without sensitive data
- [ ] Gate Interface: hardware commands executed
- [ ] Monitoring: metrics collected and visible
- [ ] Warehouse: events ingested and queryable
- [ ] API: endpoints respond correctly
- [ ] All tests passing consistently

**Story Points**: 8  
**Sprint**: 18  
**Priority**: Critical  
**Owner**: QA Engineer

---

### Story 11.7: Load Testing - Sustained & Peak

**As a** performance engineer,  
**I want to** test system at peak load,  
**so that** production readiness is confirmed.

**Acceptance Criteria**:
- [ ] Peak load test: 150+ decisions/second for 2 hours
- [ ] Latency maintained: p95 <1500ms under peak
- [ ] Error rate <1% under peak load
- [ ] No memory leaks detected
- [ ] Database connection pool stable
- [ ] Message queue throughput confirmed (1000+ events/sec)
- [ ] Warehouse ingestion keeps up with event rate
- [ ] Monitoring metrics accurate under load
- [ ] Results documented with recommendations

**Story Points**: 8  
**Sprint**: 18  
**Priority**: Critical  
**Owner**: Performance Engineer

---

### Story 11.8: Chaos Testing & Failure Scenarios

**As a** reliability engineer,  
**I want to** test system resilience under failures,  
**so that** fault-tolerance is proven.

**Acceptance Criteria**:
- [ ] Chaos test: Processor unavailable for 5 minutes
  - Circuit breaker activates ✓
  - Requests fail-fast with DENIED_TIMEOUT ✓
  - Recovery after processor comes back ✓
- [ ] Chaos test: Database down for 2 minutes
  - Config service uses cached defaults ✓
  - Requests continue with degraded performance ✓
  - Recovery after database comes back ✓
- [ ] Chaos test: Kafka down
  - Events queued in memory (not lost) ✓
  - Retry on Kafka recovery ✓
- [ ] Results documented

**Story Points**: 8  
**Sprint**: 19  
**Priority**: High  
**Owner**: Reliability Engineer

---

### Story 11.9: Documentation & Runbooks

**As a** technical writer,  
**I want to** create comprehensive documentation,  
**so that** operations team can manage the system.

**Acceptance Criteria**:
- [ ] Architecture documentation: system design, components, dependencies
- [ ] API documentation: all endpoints, request/response examples
- [ ] Configuration guide: how to set thresholds, defaults, etc.
- [ ] Operational runbooks: common issues and resolutions
- [ ] Monitoring guide: how to interpret metrics and alerts
- [ ] Troubleshooting guide: common problems and diagnosis steps
- [ ] Release notes: what's included in this version
- [ ] All documentation in markdown, version-controlled

**Story Points**: 5  
**Sprint**: 19  
**Priority**: High  
**Owner**: Technical Writer

---

### Story 11.10: Defect Triage & Resolution

**As a** engineering lead,  
**I want to** identify and resolve all defects before pilot,  
**so that** production is stable.

**Acceptance Criteria**:
- [ ] All critical defects (blocking pilot) fixed
- [ ] All high-priority defects reviewed and mitigated
- [ ] Performance issues: latency optimized
- [ ] Security issues: vulnerabilities patched
- [ ] Stability: error handling improved
- [ ] Defect tracking: all issues logged and closed
- [ ] Root cause analysis: lessons learned documented
- [ ] Pre-pilot sign-off obtained

**Story Points**: 8  
**Sprint**: 19-20  
**Priority**: Critical  
**Owner**: Engineering Lead

---

## Summary Table

| Unit | Total Stories | Person-Weeks | Est. Effort |
|------|------|--------------|------------|
| Unit-1 | 5 | 3-4 | 2 weeks |
| Unit-2 | 8 | 12-16 | 3-4 weeks |
| Unit-3 | 6 | 6-8 | 2-3 weeks |
| Unit-4 | 8 | 12-16 | 3-4 weeks |
| Unit-5 | 6 | 6-8 | 2-3 weeks |
| Unit-6 | 8 | 6-8 | 2-3 weeks |
| Unit-7 | 7 | 6-8 | 2-3 weeks |
| Unit-8 | 5 | 4-6 | 1-2 weeks |
| Unit-9 | 6 | 8-10 | 2-3 weeks |
| Unit-10 | 5 | 6-8 | 2-3 weeks |
| Unit-11 | 10 | 16-20 | 3-4 weeks |
| **TOTAL** | **74 Stories** | **87-126 person-weeks** | **24-32 weeks** |

---

## Next Steps

1. **Assign story owners** to engineering teams
2. **Estimate story points** with team consensus (planning poker)
3. **Prioritize stories** within each unit (MoSCoW method)
4. **Create sprint plan** based on unit sequencing
5. **Set definition of done** for story completion
6. **Track progress** via sprint burndown

---

**Document Version**: 1.0  
**Last Updated**: March 16, 2026  
**Status**: Ready for Sprint Planning  
**Next Phase**: Story Point Estimation & Capacity Planning
