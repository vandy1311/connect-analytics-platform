# Architecture Visualization

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      GATE HARDWARE (Entry Point)                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Card Reader → Card Data → REST API Call                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SPRING BOOT APPLICATION                        │
│                    (Authorization Service)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         REST Controller (Port 8080)                      │  │
│  │  POST /authorize/check-entry                            │  │
│  │  GET/POST /config/store/{id}                            │  │
│  │  GET /health                                            │  │
│  └────────────┬───────────────────────────────────────────┘  │
│               │                                                │
│  ┌────────────▼───────────────────────────────────────────┐  │
│  │        AuthorizationService (Core Logic)               │  │
│  │                                                         │  │
│  │  1. BIN Lookup (Card Type Detection)                  │  │
│  │  2. Get Configuration (+ Defaults)                    │  │
│  │  3. Query Processor for Balance                       │  │
│  │  4. Calculate Required Amount                         │  │
│  │  5. Decision Logic (8 paths)                          │  │
│  │  6. Handle Reversals                                  │  │
│  └────┬──────────────┬──────────────┬─────────────────┘  │
│       │              │              │                      │
│  ┌────▼──────┐  ┌───▼──────┐  ┌───▼────────┐              │
│  │ ConfigSvc │  │ Logging  │  │ Processor  │              │
│  │           │  │ Service  │  │ Client     │              │
│  │ • Cache   │  │          │  │            │              │
│  │ • Defaults│  │• Events  │  │• Mock      │              │
│  │           │  │• PCI-DSS │  │• Interface │              │
│  └────┬──────┘  └───┬──────┘  └───┬────────┘              │
│       │             │             │                        │
└───────┼─────────────┼─────────────┼──────────────────────┘
        │             │             │
        ▼             ▼             ▼
    ┌─────────┐  ┌─────────┐  ┌──────────────────┐
    │Config   │  │Event    │  │Payment Processor │
    │Store    │  │Queue    │  │Integration       │
    │(In-Mem) │  │(Kafka)  │  │(Mock or Real)    │
    └─────────┘  └─────────┘  └──────────────────┘
        │             │             │
        │             ▼             │
        │        ┌──────────────┐   │
        │        │Data Warehouse│◄──┘
        │        │(BigQuery)    │
        │        └──────────────┘
        │
        ▼
    ┌─────────────┐
    │PostgreSQL   │
    │Database     │
    │(Production) │
    └─────────────┘
```

## Decision Flow Diagram

```
                    ┌─────────────────────────┐
                    │ Authorization Request   │
                    │ (Card, Store ID)        │
                    └────────┬────────────────┘
                             │
                             ▼
                    ┌─────────────────────────┐
                    │ BIN Lookup              │
                    │ (Is Prepaid?)           │
                    └────┬──────────────┬─────┘
                    Yes  │              │ No
                         │              ▼
                         │      ┌───────────────────┐
                         │      │ DENIED            │
                         │      │ NOT_PREPAID       │
                         │      └───────────────────┘
                         │
                         ▼
                    ┌─────────────────────────┐
                    │ Get Configuration       │
                    │ (or use defaults)       │
                    └────────┬────────────────┘
                             │
                             ▼
                    ┌─────────────────────────┐
                    │ Calculate Required      │
                    │ Req = Mult × Basket     │
                    │ Req = 3.0 × $50 = $150  │
                    └────────┬────────────────┘
                             │
                             ▼
                    ┌─────────────────────────┐
                    │ Query Processor         │
                    │ Get Balance & Preauth   │
                    └────┬──────┬──────┬──────┘
                         │      │      │
                    ┌────┴──┐ ┌─┴─┐ ┌─┴───┐
                    │ Error │ │TO │ │Succ │
                    │       │ │UT │ │ess  │
                    └───┬───┘ └─┬─┘ └──┬──┘
                        │      │      │
                        ▼      ▼      ▼
                    ┌──────┐ ┌──────┐ ┌──────────────────┐
                    │DENIED│ │DENIED│ │ Compare Balance  │
                    │ERROR │ │TIMEOUT│ │ Avail >= Req?   │
                    └──────┘ └──────┘ └────┬─────────┬──┘
                                       Yes │         │ No
                                           │         │
                                      ┌────▼─┐   ┌──▼─────────────┐
                                      │APPROV│   │DENIED_INSUFF   │
                                      │ED    │   │Reverse Preauth │
                                      └──────┘   └────────────────┘
```

## Component Interaction Flow

```
User (Gateway)
     │
     │ POST /authorize/check-entry
     ▼
┌─────────────────────────────────┐
│ REST Controller                 │
└──────────┬──────────────────────┘
           │ validate & forward
           ▼
┌─────────────────────────────────┐
│ AuthorizationService            │
│ .authorize(card, store)         │
└──────────┬──────────────────────┘
           │
           ├─ calls ─────────────────────────► BIN Lookup
           │         PaymentProcessorClient     (prepaid check)
           │
           ├─ calls ─────────────────────────► Get Config
           │         ConfigurationService       (or defaults)
           │
           ├─ calls ─────────────────────────► Query Balance
           │         PaymentProcessorClient     (get available)
           │
           ├─ Decision Logic
           │  (compare available vs required)
           │
           ├─ calls ─────────────────────────► Log Event
           │         EventLogger                (async)
           │
           ├─ if insufficient
           │ calls ─────────────────────────► Reverse Preauth
           │         PaymentProcessorClient     (async)
           │
           ▼
┌─────────────────────────────────┐
│ AuthorizationResponse           │
│ {decision, balance, latency}    │
└──────────┬──────────────────────┘
           │ HTTP 200
           ▼
        Gateway → Display & Open/Close Gate
```

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                    REQUEST                              │
│  {store_id, card_data, request_id}                      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │ Validation          │
        │ • store_id ✓        │
        │ • card_data ✓       │
        │ • card_number ✓     │
        └────────┬────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │ Card Processing     │
        │ • BIN extraction    │
        │ • Tokenization      │
        │ • Masking (no log)  │
        └────────┬────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │ Core Decision       │
        │ 8 decision paths    │
        │ per unit tests      │
        └────────┬────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                    RESPONSE                             │
│  {decision, available_balance, required_balance,        │
│   decision_time_ms, reason}                             │
└─────────────────────────────────────────────────────────┘
                 │
                 ├────► Log Event (no sensitive data)
                 │      → Kafka Topic
                 │      → Data Warehouse
                 │
                 ├────► Trigger Reversal (if needed)
                 │      → Async operation
                 │
                 └────► Response to Gateway
                        → Display message
                        → Open/Close gate
```

## Test Coverage Map

```
AuthorizationService.authorize()
│
├─ Test 1: Happy Path ✓
│  ├─ Prepaid card? YES
│  ├─ Config exists? YES
│  ├─ Balance sufficient? YES
│  └─ Decision: APPROVED
│
├─ Test 2: Not Prepaid ✓
│  ├─ Prepaid card? NO
│  └─ Decision: DENIED_NOT_PREPAID
│
├─ Test 3: Insufficient Balance ✓
│  ├─ Prepaid card? YES
│  ├─ Config exists? YES
│  ├─ Balance sufficient? NO
│  ├─ Reversal triggered? YES
│  └─ Decision: DENIED_INSUFFICIENT_BALANCE
│
├─ Test 4: Processor Error ✓
│  ├─ Prepaid card? YES
│  ├─ Config exists? YES
│  ├─ Processor call succeeds? NO
│  └─ Decision: DENIED_PROCESSOR_ERROR
│
├─ Test 5: Default Config ✓
│  ├─ Prepaid card? YES
│  ├─ Config exists? NO
│  ├─ Uses defaults? YES (3x, $50)
│  └─ Decision: APPROVED/DENIED (based on balance)
│
└─ Test 6: Latency ✓
   ├─ Total decision time? < 1200ms
   └─ Performance: PASS
```

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│           Development Environment           │
│  • Local Spring Boot (port 8080)            │
│  • In-memory cache                          │
│  • Mock processor                           │
│  • Unit tests                               │
└─────────────────────────────────────────────┘

                    ▼

┌─────────────────────────────────────────────┐
│           Staging Environment               │
│  • Kubernetes deployment                    │
│  • Real processor (sandbox)                 │
│  • PostgreSQL (staging)                     │
│  • Kafka (message queue)                    │
│  • Prometheus metrics                       │
│  • Integration tests                        │
└─────────────────────────────────────────────┘

                    ▼

┌─────────────────────────────────────────────┐
│ Pilot Environment (2 stores, Oct 2026)      │
│  • Multi-zone Kubernetes                    │
│  • Real processor (prod creds)              │
│  • PostgreSQL (prod)                        │
│  • Real gate hardware                       │
│  • Monitoring enabled                       │
│  • Canary deployment (10% traffic)          │
└─────────────────────────────────────────────┘

                    ▼

┌─────────────────────────────────────────────┐
│ Production (1000+ stores, Dec 2026)         │
│  • Multi-region Kubernetes                  │
│  • Real processor                           │
│  • PostgreSQL (replicated)                  │
│  • Kafka (high-throughput)                  │
│  • BigQuery (analytics)                     │
│  • Full monitoring & alerting                │
│  • Phased rollout (10% → 25% → 50% → 100%)  │
└─────────────────────────────────────────────┘
```

---

## Key Metrics

### Latency Breakdown
```
BIN Lookup          0-200ms  |████│
Config Retrieval    0-100ms  |███│
Processor Query     50-300ms |████████────│
Decision Logic      <50ms    |█│
Reversal (async)    200ms    |████│
─────────────────────────────────────
Total (p95)         <1500ms  |████████████████│ ✅ Target
```

### Throughput Capacity
```
Decision Rate       100+ req/sec  |████████|
Queue Processing    1000+ evt/sec |████████|
Warehouse Ingestion 1000+ evt/sec |████████|
Cache Hits          95%           |████████|
```

### Error Rates
```
Approved:           60-70%  ✅
Denied (various):   20-35%  ✅
Processing Errors:  <1%     ✅
```

---

These diagrams help stakeholders understand:
1. **System Architecture** - How components interact
2. **Decision Flow** - How authorization decisions are made
3. **Component Interactions** - Service call sequence
4. **Data Flow** - What data moves through the system
5. **Test Coverage** - What scenarios are tested
6. **Deployment** - How it moves from dev to production
