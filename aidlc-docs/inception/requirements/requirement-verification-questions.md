# JWO Prepaid Card Solution - Requirements Verification Questions

**Status**: Awaiting Answers  
**Phase**: INCEPTION - Requirements Analysis  

Please answer all questions below by filling in the `[Answer]:` tags with your response (use A, B, C, D, E format for multiple choice, or write custom responses for open questions).

---

## FUNCTIONAL REQUIREMENTS

### Q1: Prepaid Card Detection Strategy
How should the system identify prepaid cards during customer entry?

A) Use card metadata/bin database lookup to identify prepaid cards before entry  
B) Check payment method at checkout and adjust authorization strategy  
C) Hybrid approach - detect at entry AND adjust at checkout  
D) Use customer profile data (if they're repeat customers with prepaid history)  
E) Other (please describe):  

[Answer]:C

---

### Q2: Preauthorization Amount Strategy
What should be the initial preauthorization amount for prepaid customers?

A) Fixed amount (e.g., $100 or $200)  
B) Estimated based on store average transaction  
C) Based on remaining customer balance on card  
D) Dynamic/higher than standard for risk mitigation  
E) Other (please describe):  

[Answer]:C

---

### Q3: Entry Prevention vs. Soft Restrictions
Should prepaid customers be completely blocked from entry, or allowed entry with disclaimers/restrictions?

A) Hard block - prepaid customers cannot enter JWO locations  
B) Allow entry but with payment guarantee requirement (e.g., deposit or backup payment method)  
C) Allow entry with risk acknowledgment/waiver  
D) Allow entry but monitor cart value in real-time  
E) Other (please describe):  

[Answer]:B

---

### Q4: Handling Insufficient Funds at Checkout
If a prepaid customer has insufficient funds at final settlement, what should happen?

A) Decline transaction, customer leaves without items  
B) Partial fulfillment - charge what's available, customer takes reduced items  
C) Hold transaction, request supplemental payment method  
D) Allow transaction, customer owes the difference (credit/invoice)  
E) Other (please describe):  

[Answer]:B

---

### Q5: Real-Time Balance Monitoring
Should the system monitor the prepaid card balance in real-time as the customer shops?

A) Yes, track balance continuously and alert customer if approaching limit  
B) No, only check at entry and at checkout  
C) Only for high-risk situations (high cart values)  
D) Depends on customer consent/opt-in  
E) Other (please describe):  

[Answer]:A

---

### Q6: Integration Points
Which payment processors/gateways need to be integrated? (List or select from known options)

A) Visa/Mastercard directly  
B) Third-party payment processor (Stripe, Square, PayPal, etc.) - which one(s)?  
C) Existing internal payment gateway (what's the name/integration method?)  
D) Multiple processors (which ones?)  
E) Other (please describe):  

[Answer]:D

---

### Q7: Customer Communication
How should customers learn about prepaid card restrictions?

A) In-store signage only  
B) Mobile app notification at entry  
C) Email/SMS notification  
D) Website announcement  
E) Other (please describe):  

[Answer]:B

---

## NON-FUNCTIONAL REQUIREMENTS

### Q8: Authorization Latency
What's the acceptable latency for preauthorization checks at entry?

A) Less than 100ms (real-time streaming)  
B) 100-500ms (fast)  
C) 500ms-2 seconds (acceptable for retail)  
D) 2-5 seconds (slower but acceptable)  
E) Other (please specify):  

[Answer]:A

---

### Q9: Availability & Reliability
Should this system work in offline mode or fail gracefully?

A) Must work 100% of the time (offline fallback required)  
B) High availability (99.9%+ uptime)  
C) Standard availability (99% uptime)  
D) Degraded mode acceptable (can deny entry, retry logic)  
E) Other (please describe):  

[Answer]:B

---

### Q10: Geographic Scope
Is this for a single store location or multiple locations?

A) Single JWO location (pilot)  
B) Multiple specific locations (which ones?)  
C) All JWO locations in a region  
D) All JWO locations globally  
E) Other (please describe):  

[Answer]:D

---

### Q11: Fraud Detection
Should the system include fraud detection for prepaid card transactions?

A) Yes, full fraud detection suite  
B) Yes, basic risk scoring for prepaid cards  
C) No, rely on payment processor's fraud detection  
D) Custom fraud rules (please describe)  
E) Other (please describe):  

[Answer]:B

---

## BUSINESS CONTEXT & CONSTRAINTS

### Q12: Compliance Requirements
Are there specific regulatory requirements for this solution?

A) PCI-DSS compliance required  
B) State/country-specific payment regulations  
C) Internal company policies only  
D) No special compliance needs  
E) Other (please describe):  

[Answer]:A

---

### Q13: Success Metrics
How will this solution be measured for success?

A) Reduction in payment declines for prepaid customers  
B) Increase in prepaid customer access/experience  
C) Reduction in fraud/chargebacks  
D) Balanced approach (all of the above)  
E) Other (please describe):  

[Answer]:D

---

### Q14: Timeline & Constraints
What's the timeline for this solution?

A) Proof of concept/MVP (weeks)  
B) Pilot at one location (months)  
C) Full rollout (months)  
D) No specific timeline, "as soon as possible"  
E) Other (please describe):  

[Answer]:A

---

### Q15: Budget/Resource Constraints
Are there specific budget or resource constraints?

A) No constraints - build the right solution  
B) Budget-constrained - minimize spend  
C) Team capacity-constrained - limited engineers available  
D) Time-constrained - quick turnaround required  
E) Other (please describe):  

[Answer]:C

---

## TECHNICAL CONTEXT

### Q16: Existing Infrastructure
What's your current payment processing infrastructure?

A) Already built (describe briefly)  
B) We use a third-party service  
C) No existing infrastructure - building from scratch  
D) Hybrid setup  
E) Other (please describe):  

[Answer]:C

---

### Q17: Technology Stack Preference
Any technology stack preferences or constraints?

A) AWS-based solution  
B) Cloud-agnostic  
C) On-premises only  
D) Microservices architecture  
E) Other (please describe):  

[Answer]:B

---

### Q18: Integration Scope
Is this a standalone service or must it integrate with existing JWO systems?

A) Standalone service  
B) Must integrate with JWO entry/exit systems  
C) Must integrate with JWO + payment processing  
D) Full integration with entire JWO ecosystem  
E) Other (please describe):  

[Answer]:D

---

### Q19: Data Requirements
What customer/transaction data needs to be retained?

A) Minimal - only for audit/compliance  
B) Standard - typical payment transaction data  
C) Enhanced - detailed customer behavior analytics  
D) Custom data retention (please specify)  
E) Other (please describe):  

[Answer]:C

---

### Q20: Extensibility
Should this solution support future enhancements?

A) Fixed feature set - no future enhancements planned  
B) Extensible for future prepaid card features  
C) Part of broader payment strategy (more features coming)  
D) Highly modular for multiple use cases  
E) Other (please describe):  

[Answer]:C

---

## IMPLEMENTATION PREFERENCES

### Q21: Solution Architecture
What's your preferred architectural approach?

A) Centralized authorization service  
B) Distributed/gateway-based approach  
C) No preference - recommend the best approach  
D) Event-driven architecture  
E) Other (please describe):  

[Answer]:C

---

### Q22: Third-party vs. Custom Development
Should this be built custom or leverage third-party solutions?

A) Custom development (full control)  
B) Third-party service (faster, less maintenance)  
C) Hybrid (third-party + custom integration)  
D) Evaluate both and recommend best option  
E) Other (please describe):  

[Answer]:C

---

---

## NEXT STEPS

Once you've answered all questions above, I will:
1. Validate answers for completeness and consistency
2. Ask follow-up questions if needed
3. Generate a comprehensive Requirements document
4. Present the complete requirements for your approval
5. Proceed to the Workflow Planning phase

Please fill in all [Answer]: fields and let me know when complete.

