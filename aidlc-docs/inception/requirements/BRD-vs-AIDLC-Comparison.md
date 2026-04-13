# JWO Prepaid Balance Check - BRD vs AIDLC Requirements Comparison

**Date**: March 16, 2026  
**Analysis**: Comparison of JWO_PREPAID_BALANCE_CHECK_BRD (Dec 2025) vs AI-DLC Requirements Specification

---

## Executive Summary

**Key Finding**: The provided BRD is significantly **narrower in scope** than the AIDLC requirements I generated. The BRD focuses on a **specific single feature** (entry gate balance check), while the AIDLC requirements encompass a **broader payment solution architecture**.

**Recommendation**: The BRD and AIDLC requirements need alignment before proceeding. The BRD should be considered the source of truth for the **entry gate balance check feature**, and AIDLC requirements should be refined to either:
1. Focus solely on the BRD scope (narrower MVP), OR
2. Expand the BRD to include the broader payment features described in AIDLC

---

## Alignment Analysis

### ✅ AREAS OF AGREEMENT

| Dimension | BRD | AIDLC Req | Status |
|---|---|---|---|
| **Prepaid Card Identification** | Yes - BIN lookup at entry gate | Yes - Hybrid detection | ✅ ALIGNED |
| **Balance-Based Decision** | Yes - threshold multiplier × average basket | Yes - card balance-based preauth | ✅ ALIGNED |
| **Entry Control** | Yes - allow/deny entry | Yes - payment guarantee requirement | ⚠️ DIFFERENT APPROACH |
| **Real-time Processing** | Yes - <1-2 second gate response | Yes - <100ms authorization | ✅ ALIGNED (BRD less strict) |
| **Compliance** | Yes - PCI compliance mentioned | Yes - PCI-DSS compliance | ✅ ALIGNED |
| **Dual Payment Method** | Yes - alternative payment on entry denial | Yes - payment guarantee method | ✅ PARTIAL ALIGNMENT |
| **Logging & Reporting** | Yes - extensive metrics/dashboards | Yes - enhanced data retention | ✅ ALIGNED |

---

### ⚠️ CRITICAL DIFFERENCES

#### 1. **Scope: Entry Gate vs. Full Payment Lifecycle**

| Aspect | BRD | AIDLC Requirement | Gap |
|---|---|---|---|
| **Focus** | Entry gate decision only | Entire payment lifecycle |  BROAD |
| **Entry Check** | Check balance, approve/deny | Check balance + require guarantee method | ⚠️ BRD doesn't mandate backup payment |
| **Mid-Shopping** | Not in scope | Real-time balance monitoring during shopping | AIDLC has, BRD doesn't |
| **Checkout** | "Standard JWO payment failure processes apply" | Partial transaction support (charge what's available) | ⚠️ BRD silent on this |
| **Failed Settlements** | Expect customer to retry with new card | System automatically tries guarantee payment | AIDLC more sophisticated |

**Issue**: AIDLC scope is **3-4x broader** than the BRD scope.

---

#### 2. **Entry Decision Logic: Different Approaches**

**BRD Approach** (Simple & Direct):
```
IF available_balance ≥ (threshold_multiplier × average_basket_size)
  THEN: Allow entry
  ELSE: Deny entry (customer tries different card)
```

**AIDLC Approach** (More Complex):
```
IF available_balance ≥ (threshold_multiplier × average_basket_size)
  THEN: Check if customer has backup payment method on file
    IF: Backup exists
      THEN: Allow entry (backup covers shortfall risk)
      ELSE: Deny entry or require adding backup method
  ELSE: Deny entry
```

**Impact**: 
- BRD: Simple binary decision
- AIDLC: Additional authentication/verification step for backup payment

**Question**: Does the BRD want to require backup payment methods? The AIDLC answers suggest YES, but BRD doesn't explicitly require this.

---

#### 3. **Insufficient Funds at Checkout: Critical Difference**

**BRD Approach**:
- "Payment will decline at final basket calculation"
- "Standard JWO payment failure processes will apply"
- Doesn't specify what happens
- Implies customer must intervene again

**AIDLC Approach**:
- Support **partial fulfillment**: Charge what's available from prepaid, apply backup payment for remainder
- Automatic payment method fallback
- Better customer experience (items not held)

**Impact**:
- BRD: Assumes customer failure at checkout is acceptable
- AIDLC: Assumes system should prevent customer failure through design

This is a **fundamental philosophy difference**.

---

#### 4. **Real-Time Balance Monitoring**

**BRD**: 
- Balance checked ONLY at entry gate
- No mention of mid-shopping monitoring
- Out of scope: "Balance checks after initial entry"

**AIDLC**:
- Requirement Q5: "Real-time balance monitoring - track balance continuously"
- Alert customer if cart approaching limit
- Prevent surprise declines at checkout

**Impact**: BRD is reactive (check at gate → accept risk of decline at exit), AIDLC is proactive (monitor throughout shopping).

---

#### 5. **Multi-Processor Integration**

**BRD**:
- Mentions "Delegated Payment providers (Stripe, Adyen, Shift4)" but lists as **out-of-scope** for P0
- P0 scope = "ptech US" only
- No requirement for multi-processor support

**AIDLC**:
- Requirement Q6: Multiple processors required
- Processor routing logic required
- Fallback processor support required

**Impact**: BRD starts narrow (single processor), AIDLC assumes multi-processor complexity from day 1.

---

#### 6. **Global Deployment**

**BRD**:
- P0 = ptech US only
- P1 = Delegated Payment providers (future)

**AIDLC**:
- Requirement Q10: "All JWO locations globally"
- Designed for worldwide rollout from start

**Impact**: BRD is phased/regional; AIDLC is global from design. This significantly affects infrastructure complexity.

---

#### 7. **Configuration**

**BRD**:
- Store-level configurable threshold multiplier
- Store-level average basket size
- Changes take effect in 5 minutes
- Default values: $50 basket, 3X multiplier
- Minimal configuration

**AIDLC**:
- Mentions "configurable" but not in depth
- More dynamic approach implied

**Impact**: BRD has detailed config requirements; AIDLC underspecifies this.

---

#### 8. **Error Handling & Failure Scenarios**

**BRD** (Comprehensive):
- Bank timeout (deny entry, notify customer)
- Balance not returned (deny entry, fail-safe)
- Missing configuration (use defaults, alert ops)
- Preauth reversal timing (immediate)

**AIDLC** (Underspecified):
- Mentions graceful degradation generally
- Doesn't detail specific error handling

**Impact**: BRD is more defensive/robust; AIDLC needs augmentation here.

---

#### 9. **Reporting & Metrics**

**BRD** (Very Detailed):
- Entry attempts tracking (story #13)
- Balance data tracking (story #14)
- Payment outcomes tracking (story #15)
- Real-time dashboard (story #24)
- Weekly store reports (story #25)
- Monthly payment outcome reports (story #26)
- Transaction log data warehouse (story #27)
- Executive summary reports (story #28)
- Configuration change history (story #29)

**AIDLC**:
- Mentions "enhanced data retention for 12 months"
- Mentions "analytics" but not detailed
- Less specific reporting requirements

**Impact**: BRD has **9 detailed reporting stories**, AIDLC has 1 requirement barely mentioned. This is a significant gap.

---

#### 10. **Customer Communication**

**BRD** (Very Specific):
- Approval: "Customer sees green approval indicator on the entry display"
- Denial: "Customer sees clear message on entry display: 'Insufficient funds available on card. Please use a different payment method.'"
- Timeout: "Payment authorization timed out. Please try again or use a different payment method."
- Balance check fail: "Unable to verify card balance. Please use a different payment method."

**AIDLC**:
- Mentions "mobile app notification" for communication
- Q7: "Mobile app notification at entry"
- Less specific messaging

**Impact**: BRD is gate/display focused; AIDLC is app-focused. Different customer experience model.

---

#### 11. **Timeline & Phasing**

**BRD**:
- P0 = December 31, 2026 (Launch by year-end)
- P1 = Post-launch within 3 months (expanded features)
- Clearly phased approach

**AIDLC**:
- MVP in weeks (4-6 week target)
- Phase 2 expansion (4-8 weeks post-MVP)
- Faster timeline but similar phasing logic

**Impact**: BRD gives deadline; AIDLC gives relative timeline. Both phased but different absolute dates.

---

## Feature-by-Feature Comparison

### Features in BRD Only (🔴 Not in AIDLC)

1. ✅ **Store Configuration Service**
   - Average basket size configuration
   - Threshold multiplier configuration
   - BRD Story #7
   - **AIDLC Gap**: Not mentioned

2. ✅ **Preauth Reversal**
   - Immediate reversal if denied
   - Funds returned within 48 hours per issuer
   - BRD Story #5, FAQ Q6
   - **AIDLC Gap**: Not detailed

3. ✅ **Entry Gate UI/UX**
   - Green approval indicator
   - Deny message on display
   - BRD Stories #4, #5
   - **AIDLC Gap**: AIDLC assumes mobile app, not gate display

4. ✅ **Detailed Reporting Structure**
   - Real-time dashboard (5-min lag) 
   - Weekly store reports with recommendations
   - Monthly payment outcome reports
   - Executive summary (quarterly)
   - BRD Stories #24-29
   - **AIDLC Gap**: Not detailed

5. ✅ **Specific Error Handling Flows**
   - Bank timeout (SLA-based)
   - Balance not returned (fail-safe)
   - Missing configuration (use defaults + alert)
   - BRD Stories #8-10
   - **AIDLC Gap**: Underspecified

### Features in AIDLC Only (🟢 Not in BRD)

1. 🟢 **Payment Guarantee Mechanism**
   - Require backup payment method for entry
   - Automatic guarantee fallback at checkout
   - **BRD Gap**: Not mentioned; BRD assumes customer failure is acceptable

2. 🟢 **Real-Time Balance Monitoring**
   - Track balance continuously during shopping
   - Alert customer approaching limit
   - **BRD Gap**: Explicitly out-of-scope ("Balance checks after initial entry")

3. 🟢 **Partial Transaction Support**
   - Split payment (prepaid + backup method)
   - Charge maximum available from prepaid
   - **BRD Gap**: Silent on this; assumes standard "decline" process

4. 🟢 **Multi-Processor Integration**
   - Visa, Mastercard, routes to specific processors
   - Fallback processor logic
   - **BRD Gap**: Out-of-scope for P0; listed as P1/future

5. 🟢 **Global Deployment Architecture**
   - Multi-region infrastructure
   - Cloud-agnostic design
   - **BRD Gap**: Phased approach (US P0, global P1)

6. 🟢 **Mobile App Integration**
   - Real-time notifications
   - Cart value visibility
   - **BRD Gap**: Focused on gate displays, not app

---

## Requirements Alignment Matrix

### 22 AIDLC Questions vs BRD Coverage

| AIDLC Q | Topic | BRD Coverage | Alignment |
|---|---|---|---|
| Q1 | Prepaid Detection (hybrid) | Partially - BIN lookup only | ⚠️ PARTIAL |
| Q2 | Preauth Amount (balance-based) | Yes - balance check | ✅ YES |
| Q3 | Entry Prevention vs Soft | Yes - but different (no guarantee) | ⚠️ DIFFERENT |
| Q4 | Insufficient Funds | Different approach (standard decline vs partial) | ❌ NO |
| Q5 | Real-Time Monitoring | Explicitly out-of-scope | ❌ NO |
| Q6 | Multi-Processor | Out-of-scope P0 | ❌ NO |
| Q7 | Communication | Different (gate vs app) | ⚠️ DIFFERENT |
| Q8 | Latency | Similar (<100ms vs 1-2s) | ✅ SIMILAR |
| Q9 | Availability | High (99.9%) vs stated SLA | ✅ YES |
| Q10 | Geographic | Different (global vs phased) | ⚠️ DIFFERENT |
| Q11 | Fraud Detection | Unspecified in BRD | ⚠️ UNCLEAR |
| Q12 | Compliance | Yes - PCI-DSS | ✅ YES |
| Q13 | Success Metrics | Yes - but uses TK placeholders | ⚠️ PARTIAL |
| Q14 | Timeline | Different (weeks vs Dec 2026) | ⚠️ DIFFERENT |
| Q15 | Capacity | Not mentioned | ⚠️ N/A |
| Q16 | Infrastructure | Different (greenfield vs gate integration) | ⚠️ DIFFERENT |
| Q17 | Tech Stack | Not specified in BRD | ⚠️ N/A |
| Q18 | Integration Scope | Different (gate system only vs full ecosystem) | ⚠️ DIFFERENT |
| Q19 | Data Retention | Yes - 2 years minimum | ✅ YES |
| Q20 | Extensibility | Yes - mentioned for future | ✅ YES |
| Q21 | Architecture | Not specified; implied simple | ⚠️ DIFFERENT |
| Q22 | Build Approach | Not addressed | ⚠️ N/A |

**Summary**: ✅ 6 full alignments, ⚠️ 13 partial/different, ❌ 3 conflicting

---

## Critical Decision Points

### Issue #1: What IS the Actual Scope?

**BRD Scope**: Entry gate balance check ONLY
- Check balance at gate
- Approve/deny entry
- Customer tries different payment if denied
- Done

**AIDLC Scope**: Full payment lifecycle with guarantees
- Check balance at gate
- Require backup payment method
- Monitor balance during shopping
- Support partial fulfillment
- More complex

**Question for you**: Which scope is correct? This is **blocking** for proceeding with design.

---

### Issue #2: How to Handle Insufficient Funds at Checkout?

**BRD Approach**: 
- Let payment decline
- Customer must intervene (provide new payment method)
- High friction, poor experience

**AIDLC Approach**:
- Automatically apply backup payment method
- Partial fulfillment (charge what's available)
- Low friction, better experience

**Question for you**: Is automatic fallback desired, or accept standard decline?

---

### Issue #3: Real-Time Balance Monitoring?

**BRD**: Not in scope
- Balance checked at entry only
- Risk of surprise declines at checkout

**AIDLC**: Required
- Monitor during shopping
- Alert customer approaching limit
- Prevent declines

**Question for you**: Should customers see their balance decreasing as they shop?

---

### Issue #4: Entry Gate Payment Guarantee vs Mobile App?

**BRD**: 
- Gate-based decision
- Gate displays messaging
- Customer tries different card at gate

**AIDLC**:
- Mobile app-based notifications
- App shows balance and restrictions
- Mobile-first UX

**Question for you**: Is this a gate-based or app-based experience?

---

### Issue #5: Multi-Processor from Day 1 or Later?

**BRD**:
- P0: Single processor (ptech US)
- P1: Multiple processors later

**AIDLC**:
- Day 1: Multiple processor support required

**Question for you**: Does MVP need multi-processor support, or add later?

---

### Issue #6: Global or Regional MVP?

**BRD**:
- P0: US only
- P1: Global expansion

**AIDLC**:
- Global from day 1

**Question for you**: Is MVP global or US-first?

---

## Recommendations

### Option A: **Adopt BRD as Source of Truth (Narrower MVP)**

Revise AIDLC requirements to match BRD:
- ✅ Focus on entry gate balance check only
- ✅ Remove real-time monitoring
- ✅ Remove partial fulfillment
- ✅ Remove multi-processor complexity (P0 single processor)
- ✅ Remove global deployment (P0 US only)
- ✅ Add detailed gate UX/messaging
- ✅ Add detailed reporting requirements
- ✅ Add detailed error handling scenarios
- ✅ Faster MVP (BRD December 31, 2026 deadline)

**Advantage**: Smaller, faster, lower-risk MVP aligned with BRD timeline  
**Disadvantage**: Less sophisticated; customer experience still has friction

---

### Option B: **Enhance BRD with AIDLC Improvements (Broader MVP)**

Expand BRD to include AIDLC features:
- ✅ Add payment guarantee requirement
- ✅ Add real-time balance monitoring
- ✅ Add partial fulfillment support
- ✅ Add multi-processor from day 1
- ✅ Add global deployment architecture
- ✅ Keep gate displays AND add mobile app
- ✅ Keep BRD reporting requirements
- ✅ Longer timeline (8 weeks+ for construction)

**Advantage**: More sophisticated, better customer experience, future-proof  
**Disadvantage**: Larger scope, later timeline, higher complexity/risk

---

### Option C: **Phased Approach (BRD then AIDLC)**

**Phase 1 (MVP) — BRD scope**:
- Entry gate balance check
- Simple threshold logic
- US-only, single processor
- Standard JWO decline process
- Target: December 31, 2026

**Phase 2 (Enhancement) — AIDLC scope**:
- Add payment guarantee requirements
- Add real-time monitoring
- Add multi-processor support
- Add global deployment
- Target: Q1/Q2 2027

**Advantage**: Quick MVP release, then enhance based on learnings  
**Disadvantage**: Multiple development cycles, slower full feature realization

---

## My Recommendation

**I recommend Option C (Phased Approach)** because:

1. **BRD is already approved** (Dec 2025 document) - don't discard it
2. **Quicker MVP release** - December 31, 2026 deadline is sooner than 8-week construction timeline
3. **Lower initial risk** - single processor, US-only, simpler logic
4. **Learnings-informed** - Phase 2 can be improved based on Phase 1 data
5. **Aligns with both** - Satisfies BRD requirement yet maintains AIDLC's sophisticated Phase 2 vision

---

## Next Steps

**Before proceeding with Application Design, please clarify:**

1. **Scope Decision**: Are we building BRD MVP or AIDLC comprehensive solution as Phase 1?
2. **Payment Guarantee**: Is backup payment method required at entry (AIDLC) or optional (BRD)?
3. **Insufficient Funds**: Auto-fallback to guarantee (AIDLC) or standard decline (BRD)?
4. **Real-Time Monitoring**: Include mid-shopping balance monitoring (AIDLC) or gate-only (BRD)?
5. **Multi-Processor**: MVP single or multiple processors?
6. **Geographic Scope**: US-only or global from start?
7. **UX Platform**: Gate displays (BRD) or mobile app (AIDLC) or both?
8. **Timeline**: Dec 2026 (BRD) or 8 weeks (AIDLC)?

**Once clarified, I will update the AIDLC requirements document accordingly and the Application Design phase will proceed with correct scope.**

