# Flex Pool Allocation Guide

## Overview
The flex pool consists of cross-trained agents who can be dynamically assigned to any queue based on demand. This guide defines when and how to activate flex pool resources.

## Flex Pool Size
- Total flex pool: 8 agents
- Minimum available at any time: 3 agents
- Maximum deployed to a single queue: 4 agents

## Activation Triggers
Flex pool agents should be activated when:
1. **Forecasted demand exceeds staffing** — WFM Agent predicts a gap of 2+ agents
2. **SLA breach in progress** — any queue below SLA threshold for 5+ minutes
3. **Abandonment rate exceeds 10%** — in any queue during peak hours
4. **Occupancy exceeds 90%** — across the floor for 15+ minutes

## Allocation Priority
When multiple queues need flex pool agents simultaneously:
1. VIP queue (highest priority — revenue impact)
2. Queue with worst SLA breach
3. Queue with highest abandonment rate
4. Queue with longest wait time

## Scheduling Rules
- Flex pool shifts: 10:00 AM to 6:00 PM (covers peak hours)
- Minimum deployment: 2-hour blocks (avoid constant reassignment)
- Agents must have 15-minute transition time between queue reassignments
- Maximum 2 queue changes per shift per agent

## Burnout Prevention
- Flex pool agents should not exceed 85% occupancy for more than 5 consecutive days
- If a flex pool agent's burnout score exceeds 0.80, remove from flex pool for 48 hours
- Rotate flex pool membership monthly — no agent should be in flex pool for more than 3 consecutive months

## Post-Deployment Review
- Track flex pool utilization weekly
- If flex pool is activated more than 3 times per week, recommend permanent staffing increase
- Document activation reason, duration, and impact on SLA recovery
