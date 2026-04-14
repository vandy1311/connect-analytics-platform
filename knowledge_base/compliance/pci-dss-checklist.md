# PCI-DSS Compliance Checklist for Contact Center Agents

## Overview
All agents handling payment information must comply with PCI-DSS (Payment Card Industry Data Security Standard). Violations are flagged automatically by Contact Lens and escalated to the compliance team.

## Prohibited Actions
1. **Never read card numbers aloud** — even if the customer provides them verbally
2. **Never write down card numbers** — on paper, sticky notes, or personal devices
3. **Never store card data** — in CRM notes, chat logs, or email
4. **Never share card data** — with other agents, supervisors, or third parties
5. **Never take screenshots** — of screens displaying card information

## Required Disclosures
Before collecting any payment information, agents MUST:
1. Inform the customer that the call is being recorded
2. State that payment information will be processed securely
3. Confirm the customer consents to proceed
4. Transfer to the secure payment IVR when available

## Violation Severity Levels
- **HIGH — PCI_VIOLATION**: Agent read card number aloud on recorded line → immediate Slack alert, supervisor review within 1 hour
- **MEDIUM — MISSING_DISCLOSURE**: Agent failed to provide required disclosure → coaching within 24 hours
- **LOW — SCRIPT_DEVIATION**: Agent deviated from approved payment script → noted in quality scorecard

## Remediation
- First PCI_VIOLATION: Mandatory retraining within 48 hours
- Second PCI_VIOLATION: Written warning + supervised calls for 2 weeks
- Third PCI_VIOLATION: Escalation to HR

## Contact Lens Detection
Contact Lens automatically detects:
- Card number patterns (16-digit sequences) in transcripts
- Missing disclosure keywords before payment processing
- Script deviation from approved payment handling flow
