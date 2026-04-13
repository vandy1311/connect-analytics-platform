# Tech Stack & Build

## Core Stack

- Java 17
- Spring Boot 3.2.3 (parent POM)
- Maven (build tool, wrapper included in `.mvn/`)
- Lombok (`@Data`, `@Slf4j`, etc.)
- Jackson for JSON serialization
- Micrometer + Spring Boot Actuator for metrics and health checks

## Testing

- JUnit 5 (jupiter)
- Mockito (mockito-core + mockito-junit-jupiter)
- Spring Boot Test (`spring-boot-starter-test`)

## Production Dependencies (planned, not yet in POC)

- PostgreSQL (persistence)
- Kafka (event streaming)
- BigQuery/Snowflake (data warehouse / analytics)
- Prometheus + Grafana (monitoring)
- Resilience4j (circuit breaker, planned for Unit-5)

## Common Commands

All commands run from `jwo-auth-service-poc/`.

```bash
# Build
mvn clean package

# Run tests
mvn test

# Run tests with coverage
mvn test jacoco:report

# Start the service (port 8080, context path /api)
mvn spring-boot:run
```

## Application Config

- `src/main/resources/application.yml`
- Server port: 8080, context path: `/api`
- Logging: INFO root, DEBUG for `com.jwo`
- Actuator endpoints exposed: health, metrics, prometheus

## Key Conventions

- Lombok is excluded from the final JAR via `spring-boot-maven-plugin` config
- Java source/target: 17
- Encoding: UTF-8
