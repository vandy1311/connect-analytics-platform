# JWO Prepaid Balance Check - Phase 1 Architecture Diagrams

**Visual Design Documentation**

**Version**: 1.0  
**Date**: March 16, 2026

---

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Entry Gate Hardware"
        CR["Card Reader"]
        DS["Display System"]
        GC["Gate Controller"]
    end
    
    subgraph "Application Layer"
        EGI["Entry Gate Interface<br/>(Adapter)"]
        AUTH["Authorization Service<br/>(Core Business Logic)"]
        CONFIG["Configuration Service<br/>(Settings Management)"]
        LOG["Logging & Monitoring<br/>(Events & Analytics)"]
    end
    
    subgraph "Integration Layer"
        PROC["Payment Processor<br/>Integration"]
    end
    
    subgraph "External Systems"
        PAYMENT["Payment Processor API<br/>(Visa/MC/Amex/Discover)"]
        WAREHOUSE["Data Warehouse<br/>(BigQuery/Snowflake)"]
        CONFIGDB["Configuration Repository<br/>(PostgreSQL)"]
    end
    
    CR -->|Card Data| EGI
    DS -->|Display Commands| EGI
    GC -->|Gate State| EGI
    
    EGI -->|Card Request| AUTH
    AUTH -->|Approval/Denial| EGI
    
    AUTH -->|Config Request| CONFIG
    CONFIG -->|Config Response| AUTH
    
    AUTH -->|Query Balance| PROC
    PROC -->|Preauth/Balance/Reverse| PAYMENT
    PAYMENT -->|Balance Response| PROC
    PROC -->|Balance Data| AUTH
    
    AUTH -->|Log Events| LOG
    LOG -->|Store Events| WAREHOUSE
    
    CONFIG -->|Load/Update| CONFIGDB
    CONFIGDB -->|Config Data| CONFIG
```

---

## Entry Request Flow (Happy Path)

```mermaid
sequenceDiagram
    participant CT as Cardholder
    participant HW as Gate Hardware
    participant EGI as Entry Gate<br/>Interface
    participant AUTH as Authorization<br/>Service
    participant CFG as Configuration<br/>Service
    participant PROC as Processor<br/>Integration
    participant LOG as Logging<br/>Service
    
    CT->>HW: Presents prepaid card
    HW->>EGI: Card read event (BIN, last_4)
    EGI->>AUTH: checkEntry(store_id, card_data)
    
    par Parallel Operations
        AUTH->>CFG: getConfig(store_id)
        CFG-->>AUTH: returns config or defaults
        AUTH->>PROC: queryBalance(card_data, amount)
        PROC-->>AUTH: approved + balance
    end
    
    AUTH->>AUTH: Calculate threshold<br/>required = 3x × $50 = $150
    AUTH->>AUTH: Compare balance: $175 ≥ $150 ✓
    AUTH-->>EGI: APPROVED decision
    
    par Async
        AUTH->>LOG: Log approval event
        LOG-->>LOG: Store to warehouse
    end
    
    EGI->>HW: Open gate command
    HW->>DS: Display approval ✓
    HW->>GC: Gate unlock
    
    CT->>HW: Enter store
    HW-->>CT: Gate opens ✓
    
    Note over AUTH,LOG: Total time: ~1-2 seconds
```

---

## Entry Denial Flow (Insufficient Funds)

```mermaid
sequenceDiagram
    participant CT as Cardholder
    participant HW as Gate Hardware
    participant EGI as Entry Gate<br/>Interface
    participant AUTH as Authorization<br/>Service
    participant CFG as Configuration<br/>Service
    participant PROC as Processor<br/>Integration
    participant LOG as Logging<br/>Service
    
    CT->>HW: Presents prepaid card<br/>(balance $125)
    HW->>EGI: Card read event
    EGI->>AUTH: checkEntry(store_id, card_data)
    
    par Parallel Operations
        AUTH->>CFG: getConfig(store_id)
        CFG-->>AUTH: config: 3x multiplier
        AUTH->>PROC: queryBalance(card_data, $150)
        PROC-->>AUTH: approved + balance: $125
    end
    
    AUTH->>AUTH: Calculate: $150 required<br/>Compare: $125 < $150 ✗
    AUTH-->>EGI: DENIED_INSUFFICIENT
    
    par Parallel Operations
        AUTH->>PROC: reversePreauth(preauth_id)
        PROC-->>AUTH: void initiated
        AUTH->>LOG: Log denial + reversal
        LOG-->>LOG: Store to warehouse
    end
    
    EGI->>HW: Keep gate closed
    HW->>DS: Display denial message<br/>"Insufficient funds..."
    
    CT->>CT: Can retry with<br/>different card
    CT->>HW: Presents another card
    
    Note over AUTH,LOG: Process repeats for new card
```

---

## Error Handling: Processor Timeout

```mermaid
sequenceDiagram
    participant CT as Cardholder
    participant HW as Gate Hardware
    participant EGI as Entry Gate<br/>Interface
    participant AUTH as Authorization<br/>Service
    participant PROC as Processor<br/>Integration
    participant LOG as Logging<br/>Service
    
    CT->>HW: Presents card
    HW->>EGI: Card read event
    EGI->>AUTH: checkEntry(store_id, card_data)
    
    AUTH->>PROC: queryBalance(card_data)
    
    Note over PROC: Processor network issue<br/>No response after 800ms
    
    PROC-->>AUTH: TimeoutException
    AUTH->>AUTH: Timeout after 800ms
    
    AUTH-->>EGI: DENIED_TIMEOUT<br/>(Fail-safe)
    
    par Parallel
        AUTH->>LOG: Log timeout error
        LOG-->>LOG: Log severity: ERROR
        NOTE over LOG: Alert ops if >10%<br/>timeouts in 5min
    end
    
    EGI->>HW: Keep gate closed
    HW->>DS: Display message<br/>"Authorization timed out<br/>Please try again..."
    
    CT->>CT: Can retry immediately
    CT->>HW: Presents card again
```

---

## Configuration Missing Handling

```mermaid
sequenceDiagram
    participant CT as Cardholder
    participant HW as Gate Hardware
    participant EGI as Entry Gate<br/>Interface
    participant AUTH as Authorization<br/>Service
    participant CFG as Configuration<br/>Service
    participant OPS as Operations<br/>Team
    
    Note over AUTH: First entry at new store<br/>No config exists
    
    CT->>HW: Presents card at new store
    HW->>EGI: Card read event (store_id=NEW-123)
    EGI->>AUTH: checkEntry(NEW-123, card_data)
    
    AUTH->>CFG: getConfig(NEW-123)
    
    Note over CFG: Config not found for NEW-123
    
    CFG-->>AUTH: CONFIG_NOT_FOUND
    AUTH->>AUTH: Use defaults:<br/>3x multiplier, $50 basket<br/>required = $150
    
    par Parallel
        AUTH->>AUTH: Continue with defaults
        AUTH->>OPS: ALERT: "Configure store NEW-123"
        OPS-->>OPS: Ops team notified<br/>to set store config
    end
    
    AUTH->>AUTH: Complete authorization<br/>with defaults
    AUTH-->>EGI: APPROVED or DENIED<br/>(based on balance vs $150)
    
    EGI->>HW: Gate opens or closes
    HW->>DS: Display result
    
    Note over AUTH,OPS: Store can be configured<br/>within <5 minutes<br/>for next customer
```

---

## Circuit Breaker State Transitions

```mermaid
stateDiagram-v2
    [*] --> CLOSED
    
    CLOSED --> OPEN: Error Rate > 50%<br/>in 1 minute
    CLOSED --> CLOSED: Success
    
    OPEN --> HALF_OPEN: After 2 minutes
    OPEN --> OPEN: New failureAfter<br/>2 min timeout
    
    HALF_OPEN --> CLOSED: Test request<br/>succeeds
    HALF_OPEN --> OPEN: Test request<br/>fails
    
    note right of CLOSED
        Normal operation
        Forward requests to processor
        Collect metrics
    end note
    
    note right of OPEN
        Error rate exceeded
        FAIL-FAST: DENY all entries
        Don't call processor
        Wait 2 minutes for recovery
    end note
    
    note right of HALF_OPEN
        Try single request
        If success → restore
        If failure → stay open
    end note
```

---

## Decision Logic State Machine

```mermaid
stateDiagram-v2
    [*] --> RECEIVE_CARD
    
    RECEIVE_CARD --> BIN_LOOKUP
    BIN_LOOKUP --> BIN_RESULT{Is Prepaid?}
    
    BIN_RESULT -->|NO| DENY_NOT_PREPAID
    BIN_RESULT -->|YES| GET_CONFIG
    
    GET_CONFIG --> CONFIG_RESULT{Config Found?}
    CONFIG_RESULT -->|NO| USE_DEFAULTS
    CONFIG_RESULT -->|YES| GET_BALANCE
    
    USE_DEFAULTS --> GET_BALANCE
    
    GET_BALANCE --> BALANCE_RESULT{Got Balance?}
    BALANCE_RESULT -->|TIMEOUT| DENY_TIMEOUT
    BALANCE_RESULT -->|ERROR| DENY_ERROR
    BALANCE_RESULT -->|NO_BALANCE| DENY_NO_BALANCE
    BALANCE_RESULT -->|YES| CALC_THRESHOLD
    
    CALC_THRESHOLD --> COMPARE{Balance ≥<br/>Threshold?}
    
    COMPARE -->|YES| APPROVE
    COMPARE -->|NO| DENY_INSUFFICIENT
    
    APPROVE --> APPROVE_ACTION["🟢 Log + Open Gate"]
    DENY_NOT_PREPAID --> DENY_ACTION["🔴 Log + Close Gate"]
    DENY_TIMEOUT --> DENY_ACTION
    DENY_ERROR --> DENY_ACTION
    DENY_NO_BALANCE --> DENY_ACTION
    DENY_INSUFFICIENT --> REVERSE["Initiate Reversal"]
    REVERSE --> DENY_ACTION
    
    APPROVE_ACTION --> [*]
    DENY_ACTION --> [*]
    
    note right of GET_CONFIG
        If config missing:
        - Use defaults (3x, $50)
        - Alert ops team
        - Continue processing
    end note
    
    note right of COMPARE
        required = threshold_multiplier × average_basket_size
        Decision: available_balance ≥ required ?
    end note
```

---

## Service Deployment Topology

```mermaid
graph TB
    subgraph "Edge Layer (Physical Location)"
        HW["🏪 Entry Gate Hardware<br/>Card Reader<br/>Display<br/>Gate Control"]
    end
    
    subgraph "Network"
        NET["🌐 HTTPS/TLS Encrypted<br/>Resilient to 5min outages"]
    end
    
    subgraph "Cloud Region (HA)"
        LB["⚖️ Load Balancer"]
        
        subgraph "Zone A"
            A1["Authorization Pod"]
            A2["Authorization Pod"]
        end
        
        subgraph "Zone B"
            B1["Authorization Pod"]
            B2["Authorization Pod"]
        end
        
        CFG["Configuration Service<br/>with Redis Cache"]
        LOG["Logging Service<br/>with Queue"]
        CACHE["Redis Cache<br/>BIN Database<br/>Config Cache"]
        QUEUE["Message Queue<br/>Events<br/>Config Changes"]
    end
    
    subgraph "Data Layer"
        DB["PostgreSQL<br/>Configuration DB"]
        WH["Data Warehouse<br/>Events & Analytics"]
    end
    
    subgraph "External"
        PROC["Payment Processor<br/>API"]
    end
    
    HW -->|HTTPS| NET
    NET -->|HTTPS| LB
    
    LB --> A1
    LB --> A2
    LB --> B1
    LB --> B2
    
    A1 --> CFG
    A2 --> CFG
    B1 --> CFG
    B2 --> CFG
    
    CFG --> CACHE
    
    A1 --> LOG
    A2 --> LOG
    B1 --> LOG
    B2 --> LOG
    
    LOG --> QUEUE
    QUEUE --> WH
    
    CFG --> DB
    DB --> CFG
    
    A1 --> PROC
    A2 --> PROC
    B1 --> PROC
    B2 --> PROC
    
    style HW fill:#FFE5B4
    style NET fill:#E6F3FF
    style A1 fill:#D4EDDA
    style A2 fill:#D4EDDA
    style B1 fill:#D4EDDA
    style B2 fill:#D4EDDA
    style CFG fill:#D1ECF1
    style LOG fill:#D1ECF1
    style CACHE fill:#E2E3E5
    style QUEUE fill:#E2E3E5
    style DB fill:#F8D7DA
    style WH fill:#F8D7DA
    style PROC fill:#FFD4D4
```

---

## Data Flow: Complete Transaction

```mermaid
graph LR
    START["📱 Customer<br/>Presents Card"] 
    
    START -->|"1. Card Read"| EGI["Entry Gate<br/>Interface"]
    
    EGI -->|"2. Card Data<br/>(BIN, Last4)"| AUTH["Authorization<br/>Service"]
    
    AUTH -->|"3. Get Config"| CFG["Configuration<br/>Service"]
    CFG -->|"4. Return Config"| AUTH
    
    AUTH -->|"5. Query Balance<br/>(Preauth)"| PROC["Payment processor<br/>Integration"]
    PROC -->|"6. API Call"| EXT["External Processor<br/>API"]
    EXT -->|"7. Balance Response"| PROC
    PROC -->|"8. Balance Data"| AUTH
    
    AUTH -->|"9. Decision<br/>(Approve/Deny)"| EGI
    
    EGI -->|"10. Gate Command"| HW["Gate Hardware<br/>Open/Close"]
    
    AUTH -->|"11. Log Event"| LOG["Logging Service"]
    LOG -->|"12. Queue Event"| QUEUE["Message Queue"]
    QUEUE -->|"13. Stream Events"| WH["Data Warehouse"]
    
    HW -->|"14. Display<br/>Message"| CUST["👤 Customer"]
    HW -->|"15. Gate Opens/<br/>Closes"| CUST
    
    style START fill:#FFE5B4
    style EGI fill:#D4EDDA
    style AUTH fill:#D4EDDA
    style CFG fill:#D1ECF1
    style PROC fill:#D1ECF1
    style EXT fill:#FFD4D4
    style LOG fill:#F8D7DA
    style QUEUE fill:#E2E3E5
    style WH fill:#F8D7DA
    style HW fill:#FFE5B4
    style CUST fill:#FFE5B4
```

---

## API Contract Overview

```mermaid
graph LR
    subgraph "Entry Gate<br/>Interface"
        GW["Gateway"]
    end
    
    subgraph "Authorization<br/>Service API"
        POST1["POST /authorize/<br/>check-entry"]
    end
    
    subgraph "Configuration<br/>Service API"
        GET1["GET /config/<br/>store/{id}"]
        POST2["POST /config/<br/>store/{id}"]
    end
    
    subgraph "Logging<br/>Service API"
        POST3["POST /events/log"]
    end
    
    subgraph "Response Types"
        RESP1["✓ Approved"]
        RESP2["✗ Denied<br/>(insufficient/<br/>timeout/error)"]
        RESP3["⚠️ Config Data"]
        RESP4["✓ Event Logged"]
    end
    
    GW -->|"Card Data"| POST1
    POST1 --> RESP1
    POST1 --> RESP2
    
    POST1 -->|"store_id"| GET1
    GET1 --> RESP3
    
    POST1 -->|"balance call"| POST2
    
    POST1 -->|"decision"| POST3
    POST3 --> RESP4
    
    style POST1 fill:#D4EDDA
    style GET1 fill:#D1ECF1
    style POST2 fill:#D1ECF1
    style POST3 fill:#F8D7DA
    style RESP1 fill:#C3E6CB
    style RESP2 fill:#F5C6CB
    style RESP3 fill:#D1ECF1
    style RESP4 fill:#FFEAA7
```

---

## Error Handling Decision Tree

```mermaid
graph TD
    START["Authorization Request"] --> BIN["BIN Lookup"]
    
    BIN -->|"Is Prepaid?"| BINY{Result}
    BINY -->|"No"| DENY1["❌ DENY_NOT_PREPAID<br/>Not prepaid card"]
    BINY -->|"Yes"| CFG["Get Store Config"]
    
    CFG -->|"Config Status"| CFGY{Result}
    CFGY -->|"Missing"| ALERT["🔔 Alert Ops<br/>Use Defaults"]
    CFGY -->|"Found"| BALANCE
    ALERT --> BALANCE["Query Processor<br/>for Balance"]
    
    BALANCE -->|"Processor Response"| BALY{Result}
    BALY -->|"Timeout"| DENY2["❌ DENY_TIMEOUT<br/>Circuit Open if sustained"]
    BALY -->|"Error"| DENY3["❌ DENY_ERROR<br/>Circuit Open if >50%"]
    BALY -->|"No Balance"| DENY4["❌ DENY_NO_BALANCE<br/>Fail-safe"]
    BALY -->|"Success"| COMPARE["Calculate Threshold<br/>& Compare"]
    
    COMPARE -->|"Balance ≥ Required"| APPROVE["✅ APPROVE<br/>Open Gate"]
    COMPARE -->|"Balance < Required"| REVERT["Initiate Reversal"]
    REVERT --> DENY5["❌ DENY_INSUFFICIENT<br/>Close Gate"]
    
    APPROVE -->|"Log Event"| END1["Event Logged"]
    DENY1 -->|"Log Event"| END2["Event Logged"]
    DENY2 -->|"Log Event"| END2
    DENY3 -->|"Log Event"| END2
    DENY4 -->|"Log Event"| END2
    DENY5 -->|"Log Event"| END2
    
    END1 --> FINAL["Complete"]
    END2 --> FINAL
    
    style START fill:#E2E3E5
    style APPROVE fill:#C3E6CB
    style DENY1 fill:#F5C6CB
    style DENY2 fill:#F5C6CB
    style DENY3 fill:#F5C6CB
    style DENY4 fill:#F5C6CB
    style DENY5 fill:#F5C6CB
    style ALERT fill:#FFF3CD
```

---

## Latency Budget Breakdown

```mermaid
gantt
    title Entry Authorization Latency (p95 target: <1500ms)
    dateFormat mm:ss
    
    section Latency Components
    Card Read & Transmission :crit, 00:00, 100ms
    BIN Lookup :active, 00:01, 200ms
    Get Config (parallel) :done, 00:01, 100ms
    Preauth Request (parallel) :crit, 00:01, 600ms
    Threshold Calculation :00:07, 50ms
    Decision Making :00:07, 50ms
    Gate Opening :crit, 00:07, 1000ms
    
    section Targets
    Target Total : target, 00:00, 1500ms
```

---

## Monitoring & Alerting Strategy

```mermaid
graph TB
    subgraph "Metrics Collection"
        M1["📊 Decision Latency<br/>p50, p95, p99"]
        M2["📊 Approval Rate<br/>% approved"]
        M3["📊 Denial Breakdown<br/>By reason"]
        M4["📊 Error Rate<br/>% errors"]
        M5["📊 Processor Health<br/>Success rate"]
        M6["📊 Circuit Breaker<br/>State"]
    end
    
    subgraph "Aggregation"
        AGG["Prometheus/<br/>Datadog"]
    end
    
    subgraph "Dashboards"
        D1["🎨 Real-time<br/>System Health"]
        D2["🎨 Per-Store<br/>Metrics"]
        D3["🎨 Processor<br/>Health"]
    end
    
    subgraph "Alerting"
        A1["🔔 High Latency<br/>p95 > 1500ms"]
        A2["🔔 High Error Rate<br/>> 5%"]
        A3["🔔 Circuit Open<br/>Processor down"]
        A4["🔔 Missing Config<br/>New store"]
        A5["🔔 Payment Timeout<br/>> 10% in 5min"]
    end
    
    M1 --> AGG
    M2 --> AGG
    M3 --> AGG
    M4 --> AGG
    M5 --> AGG
    M6 --> AGG
    
    AGG --> D1
    AGG --> D2
    AGG --> D3
    
    D1 --> A1
    D3 --> A2
    D3 --> A3
    D2 --> A4
    D3 --> A5
    
    style M1 fill:#E2E3E5
    style M2 fill:#E2E3E5
    style M3 fill:#E2E3E5
    style M4 fill:#E2E3E5
    style M5 fill:#E2E3E5
    style M6 fill:#E2E3E5
    style AGG fill:#D1ECF1
    style D1 fill:#D4EDDA
    style D2 fill:#D4EDDA
    style D3 fill:#D4EDDA
    style A1 fill:#F5C6CB
    style A2 fill:#F5C6CB
    style A3 fill:#F5C6CB
    style A4 fill:#FFF3CD
    style A5 fill:#F5C6CB
```

---

**Document Version**: 1.0  
**Last Updated**: March 16, 2026  
**Status**: Complete  
**diagrams**: 11 mermaid diagrams  
**Format**: Markdown + Mermaid (GitHub/VS Code compatible)
