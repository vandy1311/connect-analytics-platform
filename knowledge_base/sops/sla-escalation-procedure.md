# SLA Escalation Procedure v3.2

## Purpose
This document defines the escalation steps when Service Level Agreement (SLA) thresholds are breached in any queue.

## SLA Thresholds by Queue
- Sales: 80% of calls answered within 20 seconds
- Support: 70% of calls answered within 30 seconds
- Billing: 80% of calls answered within 20 seconds
- Returns: 75% of calls answered within 25 seconds
- VIP: 90% of calls answered within 15 seconds

## Escalation Levels

### Level 1 — Supervisor Alert (Automatic)
- Triggered when SLA drops below threshold for 5+ minutes
- Slack alert sent to #connect-sla-alerts
- Supervisor reviews queue health and agent availability
- Action: Reassign 1-2 agents from lower-priority queues

### Level 2 — Manager Escalation
- Triggered when SLA remains below threshold for 15+ minutes after Level 1
- Contact center manager notified via Slack and email
- Action: Activate flex pool agents, extend current shift if needed

### Level 3 — Director Escalation
- Triggered when SLA below threshold for 30+ minutes
- Director of operations notified
- Action: Emergency staffing measures, consider IVR deflection

## Break Scheduling During Peak Hours
- Peak hours: 10:00 AM to 2:00 PM
- Maximum 1 agent per queue on break during peak hours
- Breaks must be staggered with minimum 15-minute gap between agents in same queue
- Automated break scheduling system should enforce this policy
- Violation of this policy is the #1 cause of abandonment spikes

## Post-Incident Review
- All Level 2+ escalations require a post-incident review within 24 hours
- Document root cause, impact, and corrective actions
- Update this procedure if systemic issues are identified
