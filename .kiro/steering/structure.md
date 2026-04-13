# Project Structure

## Repository Layout

```
.
├── jwo-auth-service-poc/          # Spring Boot application (the actual code)
├── aidlc-docs/                    # Project planning & requirements docs
│   └── inception/
│       ├── requirements/          # PRD, BRD comparison, phase-1 requirements
│       ├── design/                # Application design, architecture diagrams
│       └── planning/              # Units planning, user stories by unit
├── aidlc-workflows/               # AIDLC process automation rules (git submodule)
├── .aidlc-rule-details/           # AIDLC rule detail files (inception, construction, etc.)
├── ARCHITECTURE-DIAGRAMS.md       # ASCII system/decision/data flow diagrams
├── PHASE-1-DELIVERABLES.md        # Phase 1 summary and status
└── DSR-SECURITY-ASSESSMENT.md     # Security assessment
```

## Application Code (`jwo-auth-service-poc/`)

Base package: `com.jwo.auth`

```
src/main/java/com/jwo/auth/
├── JwoAuthServiceApplication.java          # Spring Boot entry point
├── controller/
│   └── AuthorizationController.java        # REST endpoints
├── dto/
│   ├── AuthorizationRequest.java           # Inbound request DTO
│   └── AuthorizationResponse.java          # Outbound response DTO
├── processor/
│   ├── PaymentProcessorClient.java         # Interface (abstraction layer)
│   ├── MockPaymentProcessorClient.java     # Mock impl for dev/test
│   └── ProcessorDto.java                   # Processor-specific DTOs
├── service/
│   ├── AuthorizationService.java           # Core decision logic
│   ├── ConfigurationService.java           # Per-store config + cache
│   ├── StoreConfiguration.java             # Config model
│   └── EventLogger.java                    # PCI-DSS compliant event logging
└── _tests/
    └── AuthorizationServiceTest.java       # Unit tests (6 scenarios)
```

## Layered Architecture

- `controller/` — REST API layer. Validates input, delegates to services.
- `service/` — Business logic. AuthorizationService orchestrates the decision flow.
- `processor/` — External integration abstraction. Interface + mock. Real implementations go here.
- `dto/` — Data transfer objects for API contracts.

## API Endpoints

| Method | Path                              | Purpose                    |
|--------|-----------------------------------|----------------------------|
| POST   | `/api/v1/authorize/check-entry`   | Authorization decision     |
| GET    | `/api/v1/config/store/{storeId}`  | Get store config           |
| POST   | `/api/v1/config/store/{storeId}`  | Set store config           |
| GET    | `/api/v1/health`                  | Health check               |

## Development Units (Phase 1 — 11 units)

| Unit | Focus                          |
|------|--------------------------------|
| 1    | Configuration (CRUD, caching)  |
| 2    | Processor Integration          |
| 3    | Logging (events, warehouse)    |
| 4    | Authorization Core             |
| 5    | Resilience (circuit breaker)   |
| 6    | Gate Interface (hardware)      |
| 7    | Config API & Propagation       |
| 8    | Authorization REST API         |
| 9    | Monitoring & Dashboard         |
| 10   | Data Warehouse                 |
| 11   | E2E Testing & Validation       |
