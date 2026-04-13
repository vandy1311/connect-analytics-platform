# Project Sentinel - DSR Security Assessment

**Project**: Project Sentinel (JWO Prepaid Card Authorization Service)  
**Project ID**: 5c298853-b461-4397-bbaa-3a08fdf4b791  
**Assessment Date**: March 16, 2026  
**Current State**: Phase 1 POC (Spring Boot 3 / Java 17)  
**Planned Deployment**: EKS on AWS with ECR, S3, CloudFront, Lambda, Cognito, Bedrock, KMS

---

## Assessment Summary

| Section | In-Scope Controls | Status | Critical Findings |
|---------|-------------------|--------|-------------------|
| I. General | 22 | 🔴 Multiple gaps | 8 Release Blockers |
| II. Compute (ECR/EKS) | 29 | 🔴 Not implemented | 22 Release Blockers |
| III. Storage (S3) | 9 | 🟡 Design only | 4 Release Blockers |
| V. Network (CloudFront) | 6 | 🟡 Design only | 4 Release Blockers |
| VI. Mgmt & Governance | 5 | 🟡 Partial | 2 Release Blockers |
| VII. Machine Learning (Bedrock) | 22 | 🔴 Not implemented | 12 Release Blockers |
| IX. Security (IAM/Cognito/KMS) | 22 | 🔴 Not implemented | 14 Release Blockers |
| X. Serverless (Lambda) | 11 | 🔴 Not implemented | 7 Release Blockers |
| **Code Scanning** | Required | 🔴 Not run | **Blocker** |

---

## Code Scanning Tools Assessment

| Scanner | Required? | Status | Action Needed |
|---------|-----------|--------|---------------|
| ASH or Probe (multi-scanner) | Recommended | 🔴 Not run | Run ASH against entire repo |
| Semgrep (Java/TypeScript) | Required | 🔴 Not run | Run `semgrep --config auto` locally |
| Grype (3rd party vulns) | Required | 🔴 Not run | Run `grype dir:jwo-auth-service-poc/` |
| detect-secrets | Required | 🔴 Not run | Run `detect-secrets scan` on repo |
| Trivy (containers) | Required | 🔴 Not run | Run when Dockerfiles are created |
| Open Source License Review | Required | 🔴 Not done | Run `mvn project-info-reports:licenses` |
| npm-audit (if JS present) | Required | 🔴 Not run | Run when frontend code exists |

**Action**: Run ASH or Probe as the primary multi-scanner. At minimum, run Semgrep, Grype, and detect-secrets before delivery.

---

## I. General (22 Controls In-Scope)

### P1 - Open Source Policies
**Status**: 🔴 Response Outstanding  
**Release Blocker**: Yes  
**Finding**: No evidence of open source policy compliance review.  
**Code Evidence**: `pom.xml` uses Spring Boot 3.2.3, Lombok, Jackson, Micrometer, JUnit 5, Mockito — all Apache 2.0/MIT licensed (approved).  
**Action**: Document open source policy compliance. Verify all transitive dependencies.

### P2 - Open Source License Validation
**Status**: 🔴 Response Outstanding  
**Release Blocker**: Yes  
**Finding**: License audit not performed.  
**Code Evidence**: Dependencies in `pom.xml` appear to use approved licenses (Apache 2.0, MIT), but no formal license report generated.  
**Action**: Run `mvn site && mvn project-info-reports:licenses` and validate against approved list.

### P3 - Copyright Headers & SBOM
**Status**: 🔴 Response Outstanding  
**Release Blocker**: Yes  
**Finding**: No copyright headers in source files. No LICENSE file. No SBOM.  
**Code Evidence**: All `.java` files lack copyright headers (e.g., `AuthorizationService.java`, `AuthorizationController.java`).  
**Action**: Add AWS copyright headers to all source files. Create LICENSE file. Generate SBOM from Maven.

### SC1 - OWASP Top 10 Immunity
**Status**: 🟡 Partial  
**Release Blocker**: Yes  
**Findings**:
- ✅ Input validation present in `AuthorizationController.java` (null checks on storeId, cardData)
- 🔴 No authentication/authorization on REST endpoints (no Spring Security)
- 🔴 No rate limiting on API endpoints
- 🔴 No CSRF protection configured
- 🔴 No input sanitization beyond null checks (no length limits, no regex validation on card numbers)
- 🔴 Config endpoint `POST /config/store/{storeId}` has no access control — anyone can modify store configs
**Action**: Add Spring Security, implement authentication, add input validation (card number format, length limits), add rate limiting.

### SC2 - Data Movement Between Accounts/Regions
**Status**: 🟡 Not yet applicable  
**Release Blocker**: Yes  
**Finding**: POC is local only. Production deployment plan mentions US data residency (NFR-4). No cross-account/cross-region data movement identified in design.  
**Action**: Confirm with customer during production deployment.

### SC3 - Secrets Management
**Status**: 🔴 Not Implemented  
**Release Blocker**: Yes  
**Finding**: No secrets management solution integrated.  
**Code Evidence**: `application.yml` contains no secrets currently, but no AWS Secrets Manager or SSM Parameter Store integration exists for production secrets (DB credentials, processor API keys, etc.).  
**Action**: Integrate AWS Secrets Manager for processor API keys, DB credentials. Use SSM Parameter Store for non-sensitive config.

### SC4 - No Hardcoded Secrets
**Status**: 🟢 Pass (POC)  
**Release Blocker**: Yes  
**Finding**: No hardcoded secrets found in current codebase.  
**Code Evidence**: Scanned all source files — no API keys, passwords, tokens, or connection strings hardcoded. Mock processor uses no real credentials.  
**Action**: Run `detect-secrets scan` to confirm. Maintain this practice in production code.

### SC5 - No Sensitive Data in Logs
**Status**: 🟡 Partial  
**Release Blocker**: Yes  
**Findings**:
- ✅ `EventLogger.java` logs only decision, balance, requestId — no card data (PCI-DSS compliant design)
- ✅ `MockPaymentProcessorClient.java` masks card numbers in logs via `maskCard()` method
- 🔴 `AuthorizationService.java` line 33: `authorize()` receives full `cardNumber` parameter — if debug logging is enabled, Spring could log request parameters
- 🔴 `application.yml`: `com.jwo: DEBUG` level enabled — this MUST be set to INFO/ERROR in production
- 🔴 `AuthorizationController.java`: No explicit card data masking in error logs
**Action**: Set log level to INFO/ERROR for production. Add request/response logging filters that mask sensitive fields. Verify no card data appears in any log output.

### SC6 - No Modification of Existing Network Controls
**Status**: 🟡 Not yet applicable  
**Finding**: No infrastructure code exists yet. Design docs don't indicate modification of existing security groups/NACLs.  
**Action**: Ensure IaC (CDK/CloudFormation) creates new security groups rather than modifying existing ones.

### SC7 - X-Ray Tracing
**Status**: 🔴 Not Implemented  
**Finding**: No AWS X-Ray integration in the application.  
**Action**: Add X-Ray SDK to Spring Boot app. Enable X-Ray on Lambda functions and EKS services.

### SC8 - Security Code Scanners
**Status**: 🔴 Not Run  
**Release Blocker**: Yes  
**Finding**: No evidence of any security scanner execution.  
**Action**: Run ASH/Probe or individual scanners (Semgrep, Grype, detect-secrets). Remediate Critical/High findings.

### SC9 - Regulated Data (PCI/HIPAA/GDPR)
**Status**: 🔴 Response Outstanding  
**Release Blocker**: Yes  
**Finding**: This solution WILL handle PCI data (payment card numbers) in production. PCI-DSS compliance is explicitly required per NFR-3.  
**Action**: This must be flagged — a security consultant should assist with PCI-DSS architecture review. The design documents acknowledge PCI-DSS requirements but implementation is incomplete.

### SC10 - No Binaries/Container Images in Deliverable
**Status**: 🟢 Pass  
**Release Blocker**: Yes  
**Finding**: Current deliverable is source code only. `pom.xml` defines dependencies; no binaries or container images are included.  
**Action**: Ensure deployment docs instruct customer to build from source.

### R1 - Rollback Mechanisms
**Status**: 🔴 Not Implemented  
**Finding**: No deployment rollback mechanism defined. No CloudFormation/CDK stack with rollback capability exists yet.  
**Action**: Implement IaC with rollback support. Define deployment rollback procedures.

### R2 - Resource Documentation
**Status**: 🟡 Partial  
**Finding**: Architecture docs exist (`ARCHITECTURE-DIAGRAMS.md`, `application-design-phase1.md`) but no enumeration of AWS resources created by the solution.  
**Action**: Create resource inventory document listing all AWS resources the solution creates.

### R3 - Idempotent Deployments
**Status**: 🔴 Not Tested  
**Finding**: No IaC exists to test idempotency.  
**Action**: Ensure CloudFormation/CDK stacks are idempotent when created.

### R4 - Concurrent Deployment Prevention
**Status**: 🔴 Not Implemented  
**Finding**: No deployment locking mechanism.  
**Action**: Implement deployment locks (e.g., CloudFormation stack policies, DynamoDB lock table).

### R5 - No Mutation of Pre-existing Stacks
**Status**: 🟡 Not yet applicable  
**Finding**: No IaC exists yet.  
**Action**: Ensure IaC creates new resources only.

### EN1 - Encryption at Rest
**Status**: 🔴 Not Implemented  
**Finding**: No encryption configuration for any data stores. POC uses in-memory storage only.  
**Action**: Enable encryption at rest for S3 (SSE-KMS), EBS volumes, any databases. Use KMS CMK where required.

### EN2 - Encryption in Transit
**Status**: 🔴 Not Implemented  
**Finding**: POC runs on HTTP (port 8080, no TLS). `application.yml` has no SSL/TLS configuration.  
**Action**: Configure TLS 1.2+ for all service communication. Enable HTTPS on Spring Boot. Ensure all AWS service communication uses TLS.

### EN3 - VPC Endpoints for Serverless
**Status**: 🔴 Not Implemented  
**Finding**: No VPC or VPC endpoint configuration exists.  
**Action**: Create VPC endpoints for Lambda, S3, Bedrock, and other serverless services accessed from within VPC.

### EN4 - Sensitive Data Encryption at Rest
**Status**: 🔴 Not Implemented  
**Release Blocker**: Yes  
**Finding**: Card data handling requires encryption. No encryption strategy implemented.  
**Action**: Implement field-level encryption for sensitive data. Use KMS for key management.

---

## II. Compute - ECR (1 Control In-Scope)

### ECR1 - Registry Not Public
**Status**: 🔴 Not Implemented  
**Release Blocker**: Yes  
**Finding**: No ECR repository exists yet.  
**Action**: When creating ECR, ensure `imageScanningConfiguration` is enabled and repository is PRIVATE. Block public access.

---

## II. Compute - EKS (29 Controls In-Scope)

**Overall Status**: 🔴 No EKS infrastructure exists. All 29 controls are unaddressed.

**Critical Release Blockers** (must address before delivery):

| ID | Control | Priority |
|----|---------|----------|
| EKS1 | Private Kubernetes API endpoint | Release Blocker |
| EKS2 | Control plane logs enabled | Release Blocker |
| EKS3 | Security groups restrict to port 443 only | Release Blocker |
| EKS4 | Latest stable Kubernetes version | Release Blocker |
| EKS7 | Self-service namespace provisioning | Release Blocker |
| EKS8 | IRSA for AWS resource access | Release Blocker |
| EKS9 | RBAC enabled | Release Blocker |
| EKS12 | Least privilege IAM for AWS resources | Release Blocker |
| EKS13 | Private cluster endpoint | Release Blocker |
| EKS14 | Restrict instance profile access | Release Blocker |
| EKS15 | Non-root containers | Release Blocker |
| EKS18 | KMS envelope encryption for secrets | Release Blocker |
| EKS22 | SSM instead of SSH | Release Blocker |
| EKS24 | Container image vulnerability scanning | Release Blocker |
| EKS25 | Trusted HelmChart source | Release Blocker |
| EKS26 | Hardened container images | Release Blocker |
| EKS27 | Hardened Kubernetes on EKS | Release Blocker |
| EKS28 | Customer code execution mechanism | Release Blocker |
| EKS29 | IAM roles instead of IAM users | Release Blocker |

**Action**: Create comprehensive EKS security baseline IaC covering all 29 controls. Use EKS Best Practices Guide as reference.

---

## III. Storage - S3 (9 Controls In-Scope)

| ID | Control | Status | Blocker |
|----|---------|--------|---------|
| S1 | Access logging on S3 buckets | 🔴 Not implemented | No |
| S2 | Block public access | 🔴 Not implemented | No |
| S3 | Encryption (SSE-KMS/SSE-C) | 🟡 Design mentions SSE | Yes |
| S5 | CloudFront OAC for S3 origin | 🔴 Not implemented | Yes |
| S6 | Static website hosting headers | 🔴 Not implemented | No |
| S7 | Object lock for retention | 🔴 Not implemented | No |
| S8 | Lifecycle policies | 🔴 Not implemented | No |
| S11 | Amazon Macie for PII discovery | 🔴 Not implemented | No |
| S12 | Anti-sniping controls | 🔴 Not implemented | No |

**Action**: Implement S3 bucket policies with block public access, SSE-KMS encryption, access logging, lifecycle policies, and OAC for CloudFront.

---

## V. Network & Delivery - CloudFront (6 Controls In-Scope)

| ID | Control | Status | Blocker |
|----|---------|--------|---------|
| CFR1 | Geo-restriction rules | 🔴 Not implemented | No |
| CFR2 | AWS WAF on CloudFront | 🔴 Not implemented | No |
| CFR3 | Access logging enabled | 🔴 Not implemented | Yes |
| CFR4 | HTTPS required, TLS 1.2+ | 🔴 Not implemented | Yes |
| CFR5 | TLS for non-AWS origins | 🔴 Not implemented | Yes |
| CFR6 | Origin Access Control (OAC) | 🔴 Not implemented | Yes |

**Action**: Configure CloudFront with HTTPS-only, TLS 1.2+, OAC, WAF, access logging, and geo-restrictions.

---

## VI. Management & Governance (5 Controls In-Scope)

| ID | Control | Status | Blocker |
|----|---------|--------|---------|
| CFN2 | No sensitive data in CloudFormation params | 🟡 No IaC yet | Yes |
| CT1 | CloudTrail compliance logging | 🔴 Not implemented | No |
| CW1 | No sensitive data in CloudWatch logs | 🟡 Partial (see SC5) | Yes |
| CW2 | CloudWatch Alarms | 🔴 Not implemented | No |
| CW3 | Disable DEBUG logs in production | 🔴 DEBUG enabled in application.yml | No |

**Code Finding for CW3**:
```yaml
# application.yml - MUST CHANGE FOR PRODUCTION
logging:
  level:
    root: INFO
    com.jwo: DEBUG  # ← CHANGE TO INFO OR ERROR
```

**Action**: Create production application profile with INFO/ERROR log levels. Implement CloudWatch alarms. Enable CloudTrail.

---

## VII. Machine Learning - Bedrock (22 Controls In-Scope)

**Overall Status**: 🔴 No Bedrock implementation exists in the codebase.

**Critical Release Blockers**:

| ID | Control | Status |
|----|---------|--------|
| BR3 | Restrict RAG data isolation | 🔴 Not implemented |
| BR5 | Content filters for harmful categories | 🔴 Not implemented |
| BR6 | Content filters for prompt attacks | 🔴 Not implemented |
| BR8 | Profanity filter | 🔴 Not implemented |
| BR9 | PII filters | 🔴 Not implemented |
| BR10 | Guardrail intervention alerting | 🔴 Not implemented |
| BRA1 | Agent least privilege role | 🔴 Not implemented |
| BRA3 | Agent logging | 🔴 Not implemented |
| BRA5 | Agent guardrails | 🔴 Not implemented |
| BRKB2 | CMK for transient data | 🔴 Not implemented |
| BRKB3 | Data retention policy | 🔴 Not implemented |

**Action**: When implementing Bedrock, create Guardrails with content filters (harmful categories, prompt attacks, profanity, PII). Configure model invocation logging. Use least-privilege IAM roles for agents.

---

## IX. Security & Compliance (22 Controls In-Scope)

### IAM (11 Controls)

**Overall Status**: 🔴 No IAM policies exist.

**Critical Findings**:
- No IAM roles defined for any service
- No permissions boundaries
- No least-privilege policies
- No confused deputy protections (SourceArn/SourceAccount)

**Action**: Create IAM roles with least-privilege for: EKS node groups, Lambda functions, Bedrock agents, S3 access, CloudWatch logging. Use permissions boundaries. Add SourceArn conditions on cross-service policies.

### Cognito (6 Controls)

| ID | Control | Status | Blocker |
|----|---------|--------|---------|
| COG1 | Password policy | 🔴 Not implemented | Yes |
| COG2 | MFA | 🔴 Not implemented | No |
| COG3 | Disable self-registration | 🔴 Not implemented | Yes |
| COG4 | AdvancedSecurityMode | 🔴 Not implemented | No |
| COG6 | Identity pool least privilege | 🔴 Not implemented | Yes |
| COG8 | No unauthenticated access | 🔴 Not implemented | Yes |

**Action**: Configure Cognito User Pool with strong password policy, MFA, AllowAdminCreateUserOnly=true, AdvancedSecurityMode=ENFORCE. Restrict identity pool roles.

### KMS (6 Controls)

| ID | Control | Status | Blocker |
|----|---------|--------|---------|
| KMS1 | CMK over service-managed keys | 🔴 Not implemented | No |
| KMS2 | CMK policy least privilege | 🔴 Not implemented | Yes |
| KMS3 | Cross-account CMK restrictions | 🔴 Not implemented | No |
| KMS4 | Encryption context | 🔴 Not implemented | No |
| KMS5 | Key rotation | 🔴 Not implemented | No |
| KMS7 | KMS event monitoring | 🔴 Not implemented | No |

**Action**: Create CMK for data encryption. Implement key policies with least privilege. Enable automatic key rotation. Configure EventBridge rules for KMS events.

---

## X. Serverless - Lambda (11 Controls In-Scope)

**Overall Status**: 🔴 No Lambda functions exist.

**Critical Release Blockers**:

| ID | Control | Status |
|----|---------|--------|
| L2 | Third-party library license validation | 🔴 Not done |
| L3 | No sensitive data in Lambda logs | 🔴 Not implemented |
| L4 | Secrets Manager for env vars | 🔴 Not implemented |
| L7 | Unique IAM role per function | 🔴 Not implemented |
| L8 | Least privilege execution roles | 🔴 Not implemented |
| L9 | On-failure destinations | 🔴 Not implemented |
| L12 | Secure container image storage | 🔴 Not implemented |

**Action**: When implementing Lambda functions, create unique IAM execution roles per function with least privilege. Use Secrets Manager for sensitive env vars. Configure DLQs for async invocations.

---

## Specific Code-Level Findings

### Finding 1: No Authentication on REST API (CRITICAL)
**File**: `AuthorizationController.java`  
**Issue**: All endpoints are publicly accessible with no authentication.
```java
@PostMapping("/authorize/check-entry")  // No @PreAuthorize, no security filter
public ResponseEntity<AuthorizationResponse> checkEntry(@RequestBody AuthorizationRequest request) {
```
**Risk**: Anyone can call the authorization endpoint and the config management endpoint.  
**Remediation**: Add Spring Security with JWT/OAuth2 authentication. Protect config endpoints with role-based access.

### Finding 2: Card Number Passed in Plaintext (HIGH)
**File**: `AuthorizationService.java` line 33  
**Issue**: Full card number is passed as a method parameter and used in processing.
```java
public AuthorizationResponse authorize(String cardNumber, String cardNetwork, String storeId, String requestId) {
```
**Risk**: Card number could appear in stack traces, debug logs, or memory dumps.  
**Remediation**: Tokenize card number at the controller layer before passing to service. Only pass token + last 4 digits.

### Finding 3: DEBUG Logging Enabled (MEDIUM)
**File**: `application.yml`  
**Issue**: `com.jwo: DEBUG` enables verbose logging that could expose sensitive data.
```yaml
logging:
  level:
    com.jwo: DEBUG
```
**Remediation**: Create separate `application-prod.yml` with `com.jwo: INFO` or `ERROR`.

### Finding 4: No TLS Configuration (HIGH)
**File**: `application.yml`  
**Issue**: Server runs on HTTP port 8080 with no SSL/TLS.
```yaml
server:
  port: 8080
```
**Remediation**: Configure TLS in production profile or terminate TLS at load balancer/ingress.

### Finding 5: Unused Caffeine Import (LOW)
**File**: `ConfigurationService.java`  
**Issue**: Imports `com.github.benmanes.caffeine.cache.*` but uses custom cache implementation. This dependency isn't in `pom.xml` and would cause compilation failure.
```java
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
```
**Remediation**: Remove unused imports.

### Finding 6: No Input Length Validation (MEDIUM)
**File**: `AuthorizationController.java`  
**Issue**: No validation on card number length/format, store ID length, or request ID format.  
**Risk**: Potential for injection attacks or buffer overflow in downstream systems.  
**Remediation**: Add `@Size`, `@Pattern` annotations or manual validation for all input fields.

---

## Priority Remediation Roadmap

### Phase A: Immediate (Before Any Code Delivery)
1. Run security scanners (ASH/Semgrep/Grype/detect-secrets)
2. Add copyright headers and LICENSE file
3. Generate SBOM and license report
4. Fix DEBUG logging for production
5. Remove unused Caffeine imports
6. Add input validation (card number format, length limits)
7. Add Spring Security authentication to all endpoints

### Phase B: Before Production Deployment
1. Implement all EKS security controls (29 items)
2. Configure IAM roles with least privilege
3. Set up Cognito with password policy, MFA, no self-registration
4. Enable encryption at rest (KMS CMK) and in transit (TLS 1.2+)
5. Configure VPC endpoints for serverless services
6. Enable CloudTrail, CloudWatch alarms, access logging
7. Implement Bedrock Guardrails (content filters, PII, profanity)

### Phase C: Before Security Review Sign-off
1. Complete all Release Blocker items (73 total)
2. Attach scanner results to DSR ticket
3. Document all AWS resources created
4. Verify PCI-DSS compliance with security consultant
5. Complete all "Discuss with reviewer" items

---

## Control Counts

| Category | Total In-Scope | Release Blockers | Addressed | Gaps |
|----------|---------------|-----------------|-----------|------|
| I. General | 22 | 12 | 2 | 20 |
| II. Compute | 29 | 22 | 0 | 29 |
| III. Storage | 9 | 4 | 0 | 9 |
| V. Network | 6 | 4 | 0 | 6 |
| VI. Mgmt & Gov | 5 | 2 | 0 | 5 |
| VII. ML/Bedrock | 22 | 12 | 0 | 22 |
| IX. Security | 22 | 14 | 0 | 22 |
| X. Serverless | 11 | 7 | 0 | 11 |
| **TOTAL** | **126** | **77** | **2** | **124** |

**Overall DSR Readiness**: 🔴 1.6% (2/126 controls addressed)
