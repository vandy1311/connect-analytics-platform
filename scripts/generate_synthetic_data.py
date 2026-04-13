#!/usr/bin/env python3
"""
Synthetic data generator for Connect Analytics Platform.

Generates:
- 10,000 CTR records (Parquet, partitioned year/month/day)
- 50,000 Agent Event records (Parquet, partitioned year/month/day)
- 10,000 Contact Lens records (JSON, partitioned year/month/day)

Embeds reproducible demo patterns:
- SLA breaches at 2pm
- Negative sentiment spikes on Mondays
- Burnout signals for Agent-017, Agent-023, Agent-031

Usage:
    python scripts/generate_synthetic_data.py [--output-dir output]
"""

import argparse
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Deterministic seed for reproducible output
# ---------------------------------------------------------------------------
SEED = 42
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NUM_CTR = 10_000
NUM_AGENT_EVENTS = 50_000
NUM_CONTACT_LENS = 10_000

QUEUE_NAMES = ["Sales", "Support", "Billing", "Returns", "VIP"]
# 25 agents total. IDs include the 3 required burnout agents (017, 023, 031).
# Use agents 001-022 + 023 + 025 is replaced by 031 to keep exactly 25.
_base_ids = [f"Agent-{i:03d}" for i in range(1, 25)]  # Agent-001 to Agent-024
_base_ids.append("Agent-031")  # Replace would-be Agent-025 with Agent-031
AGENT_IDS = sorted(_base_ids)  # 25 agents, includes 017, 023, 031
AGENT_NAMES = {aid: fake.name() for aid in AGENT_IDS}

BURNOUT_AGENTS = {"Agent-017", "Agent-023", "Agent-031"}

OUTCOMES = ["CONNECTED", "ABANDONED", "TRANSFERRED"]
STATES = ["AVAILABLE", "ON_CONTACT", "AFTER_CONTACT_WORK", "OFFLINE"]
EVENT_TYPES = ["STATE_CHANGE", "HEART_BEAT"]

SENTIMENTS = ["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"]
CATEGORIES = ["Escalation", "Billing", "Compliance", "General Inquiry", "Technical Support"]
COMPLIANCE_FLAGS = ["MISSING_DISCLOSURE", "PCI_VIOLATION", "SCRIPT_DEVIATION", ""]

TRANSCRIPT_EXCERPTS = [
    "Customer expressed frustration with billing charges.",
    "Agent resolved the issue quickly and professionally.",
    "Customer requested to speak with a supervisor.",
    "Agent provided clear instructions for the return process.",
    "Customer was satisfied with the resolution provided.",
    "Agent failed to disclose required terms and conditions.",
    "Customer reported unauthorized charges on their account.",
    "Agent escalated the call to the compliance team.",
    "Customer praised the quick response time.",
    "Agent struggled to find the correct information.",
    "Customer threatened to cancel their subscription.",
    "Agent offered a discount to retain the customer.",
    "Customer asked about the refund policy.",
    "Agent confirmed the payment was processed successfully.",
    "Customer was confused about the service agreement.",
]

# Date range: 14 days of data
BASE_DATE = datetime(2024, 1, 8)  # A Monday
DATE_RANGE_DAYS = 14


# ---------------------------------------------------------------------------
# Helper: partition path
# ---------------------------------------------------------------------------
def partition_path(dt: datetime) -> str:
    return f"year={dt.year}/month={dt.month:02d}/day={dt.day:02d}"


# ---------------------------------------------------------------------------
# Helper: shift schedule — staggered 8hr shifts for 25 agents
# ---------------------------------------------------------------------------
def get_shift_start_hour(agent_id: str) -> int:
    """Staggered 8hr shifts: agents start at 6, 7, 8, 9, or 10."""
    idx = int(agent_id.split("-")[1]) - 1
    return 6 + (idx % 5)


# ---------------------------------------------------------------------------
# CTR Generation
# ---------------------------------------------------------------------------
def generate_ctr_records(num_records: int) -> pd.DataFrame:
    """Generate CTR records with embedded demo patterns."""
    records = []

    for _ in range(num_records):
        day_offset = np.random.randint(0, DATE_RANGE_DAYS)
        dt = BASE_DATE + timedelta(days=day_offset)

        # Peak hours: 10am-2pm get 3x volume via weighted hour selection
        hour_weights = np.ones(24)
        hour_weights[10:14] = 3.0  # 3x volume 10am-2pm
        hour_weights[:6] = 0.1     # minimal overnight
        hour_weights[22:] = 0.1
        hour_weights = hour_weights / hour_weights.sum()
        hour = np.random.choice(24, p=hour_weights)

        minute = np.random.randint(0, 60)
        second = np.random.randint(0, 60)
        initiation_ts = dt.replace(hour=hour, minute=minute, second=second)

        queue_name = np.random.choice(QUEUE_NAMES)
        agent_id = np.random.choice(AGENT_IDS)

        # Queue duration: baseline ~30s, spikes at 2pm
        if hour == 14:
            queue_duration = max(0, int(np.random.normal(120, 40)))
        else:
            queue_duration = max(0, int(np.random.normal(30, 15)))

        # Handle time: mean 7 min (420s), std 120s
        handle_time = max(60, int(np.random.normal(420, 120)))

        connected_ts = initiation_ts + timedelta(seconds=queue_duration)
        disconnect_ts = connected_ts + timedelta(seconds=handle_time)

        # Outcome: 5% abandonment baseline, 18% spike at 2pm, 8% transfer
        if hour == 14:
            outcome_probs = [0.72, 0.20, 0.08]  # ~18% abandon at 2pm (slightly over to hit target after sampling)
        else:
            outcome_probs = [0.87, 0.05, 0.08]  # 5% abandon baseline

        outcome = np.random.choice(OUTCOMES, p=outcome_probs)

        # SLA: met if queue_duration < 20s for most queues
        sla_threshold = 20
        service_level_met = queue_duration <= sla_threshold

        # At 2pm, force more SLA breaches
        if hour == 14 and np.random.random() < 0.4:
            service_level_met = False

        records.append({
            "contact_id": str(uuid.uuid4()),
            "queue_name": queue_name,
            "agent_id": agent_id,
            "initiation_timestamp": initiation_ts.isoformat(),
            "connected_timestamp": connected_ts.isoformat() if outcome == "CONNECTED" else None,
            "disconnect_timestamp": disconnect_ts.isoformat(),
            "queue_duration_seconds": queue_duration,
            "handle_time_seconds": handle_time if outcome == "CONNECTED" else 0,
            "outcome": outcome,
            "service_level_met": service_level_met,
            "year": str(dt.year),
            "month": f"{dt.month:02d}",
            "day": f"{dt.day:02d}",
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Agent Event Generation
# ---------------------------------------------------------------------------
def generate_agent_event_records(num_records: int) -> pd.DataFrame:
    """Generate Agent Event records with state machine and burnout patterns."""
    records = []
    records_per_agent = num_records // len(AGENT_IDS)
    remainder = num_records % len(AGENT_IDS)

    for agent_idx, agent_id in enumerate(AGENT_IDS):
        agent_record_count = records_per_agent + (1 if agent_idx < remainder else 0)
        shift_start = get_shift_start_hour(agent_id)
        shift_end = shift_start + 8

        is_burnout = agent_id in BURNOUT_AGENTS

        for _ in range(agent_record_count):
            day_offset = np.random.randint(0, DATE_RANGE_DAYS)
            dt = BASE_DATE + timedelta(days=day_offset)

            # Hour within shift
            hour = np.random.randint(shift_start, min(shift_end, 23))
            minute = np.random.randint(0, 60)
            second = np.random.randint(0, 60)
            event_ts = dt.replace(hour=hour, minute=minute, second=second)

            # State machine: Available → OnContact → ACW → Available
            # Burnout agents spend more time ON_CONTACT and less AVAILABLE
            if is_burnout:
                state_probs = [0.10, 0.55, 0.30, 0.05]
            else:
                state_probs = [0.30, 0.40, 0.20, 0.10]

            # At 2pm, 2 agents go on break (OFFLINE) simultaneously
            if hour == 14 and agent_id in ["Agent-001", "Agent-002"]:
                current_state = "OFFLINE"
            else:
                current_state = np.random.choice(STATES, p=state_probs)

            event_type = "STATE_CHANGE" if np.random.random() < 0.7 else "HEART_BEAT"

            # State duration
            if current_state == "AVAILABLE":
                state_duration = max(1, int(np.random.normal(60, 20)))
            elif current_state == "ON_CONTACT":
                state_duration = max(30, int(np.random.normal(420, 120)))
            elif current_state == "AFTER_CONTACT_WORK":
                state_duration = max(10, int(np.random.normal(90, 30)))
            else:  # OFFLINE
                state_duration = max(60, int(np.random.normal(900, 300)))

            # Contacts handled today: proportional to hours into shift
            hours_into_shift = max(1, hour - shift_start)
            contacts_base = hours_into_shift * 4  # ~4 contacts/hour
            contacts_handled = max(0, int(np.random.normal(contacts_base, 2)))

            # Occupancy rate
            # Baseline 75%, burnout agents >92% for 8+ days
            if is_burnout:
                # Agent-023 and Agent-031: occupancy >92% for 8 days
                if agent_id in ("Agent-023", "Agent-031"):
                    occupancy = min(1.0, max(0.92, np.random.normal(0.95, 0.02)))
                else:
                    # Agent-017: high occupancy but also negative calls
                    occupancy = min(1.0, max(0.88, np.random.normal(0.93, 0.03)))
            elif hour == 14:
                # 95%+ peaks at 2pm for everyone
                occupancy = min(1.0, max(0.90, np.random.normal(0.96, 0.02)))
            else:
                occupancy = min(1.0, max(0.0, np.random.normal(0.75, 0.10)))

            records.append({
                "event_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "agent_name": AGENT_NAMES[agent_id],
                "event_type": event_type,
                "current_state": current_state,
                "state_start_timestamp": event_ts.isoformat(),
                "state_duration_seconds": state_duration,
                "contacts_handled_today": contacts_handled,
                "occupancy_rate": round(occupancy, 4),
                "year": str(dt.year),
                "month": f"{dt.month:02d}",
                "day": f"{dt.day:02d}",
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Contact Lens Generation
# ---------------------------------------------------------------------------
def generate_contact_lens_records(num_records: int) -> list[dict]:
    """Generate Contact Lens records with sentiment patterns."""
    records = []

    # Track Agent-017 negative call count to ensure ≥4
    agent_017_negative_count = 0

    for i in range(num_records):
        day_offset = np.random.randint(0, DATE_RANGE_DAYS)
        dt = BASE_DATE + timedelta(days=day_offset)
        hour = np.random.randint(8, 20)
        minute = np.random.randint(0, 60)
        second = np.random.randint(0, 60)
        analysis_ts = dt.replace(hour=hour, minute=minute, second=second)

        agent_id = np.random.choice(AGENT_IDS)

        # Sentiment distribution: 60% positive, 25% neutral, 15% negative
        # Monday spike: increase negative to ~25% on Mondays
        is_monday = dt.weekday() == 0

        if agent_id == "Agent-017" and agent_017_negative_count < 4 and i < num_records - 100:
            # Force negative sentiment for Agent-017 (need ≥4)
            overall_sentiment = "NEGATIVE"
            agent_017_negative_count += 1
        elif is_monday:
            sentiment_probs = [0.45, 0.25, 0.20, 0.10]  # more negative on Mondays
        else:
            sentiment_probs = [0.60, 0.15, 0.15, 0.10]  # baseline

        if not (agent_id == "Agent-017" and agent_017_negative_count <= 4 and overall_sentiment == "NEGATIVE" if 'overall_sentiment' in dir() else False):
            if is_monday:
                overall_sentiment = np.random.choice(SENTIMENTS, p=[0.45, 0.25, 0.20, 0.10])
            else:
                overall_sentiment = np.random.choice(SENTIMENTS, p=[0.60, 0.15, 0.15, 0.10])

        # Track Agent-017 negatives from random assignment too
        if agent_id == "Agent-017" and overall_sentiment == "NEGATIVE":
            agent_017_negative_count += 1

        # Sentiment scores
        if overall_sentiment == "POSITIVE":
            customer_score = round(np.random.uniform(1.0, 5.0), 2)
            agent_score = round(np.random.uniform(1.0, 5.0), 2)
        elif overall_sentiment == "NEGATIVE":
            customer_score = round(np.random.uniform(-5.0, -1.0), 2)
            agent_score = round(np.random.uniform(-3.0, 2.0), 2)
        elif overall_sentiment == "NEUTRAL":
            customer_score = round(np.random.uniform(-1.0, 1.0), 2)
            agent_score = round(np.random.uniform(-1.0, 1.0), 2)
        else:  # MIXED
            customer_score = round(np.random.uniform(-3.0, 3.0), 2)
            agent_score = round(np.random.uniform(-2.0, 2.0), 2)

        # Categories: Escalation, Billing, Compliance hits
        num_categories = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
        categories = list(np.random.choice(CATEGORIES, size=num_categories, replace=False)) if num_categories > 0 else []

        # Compliance flags: ~5% of records have flags
        if np.random.random() < 0.05:
            flags = [np.random.choice(["MISSING_DISCLOSURE", "PCI_VIOLATION", "SCRIPT_DEVIATION"])]
        else:
            flags = []

        transcript = np.random.choice(TRANSCRIPT_EXCERPTS)

        records.append({
            "contact_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "overall_sentiment": overall_sentiment,
            "customer_sentiment_score": customer_score,
            "agent_sentiment_score": agent_score,
            "categories": categories,
            "transcript_excerpt": transcript,
            "compliance_flags": flags,
            "analysis_timestamp": analysis_ts.isoformat(),
            "year": str(dt.year),
            "month": f"{dt.month:02d}",
            "day": f"{dt.day:02d}",
        })

    # Ensure Agent-017 has ≥4 negative calls by patching if needed
    if agent_017_negative_count < 4:
        agent_017_records = [r for r in records if r["agent_id"] == "Agent-017"]
        needed = 4 - agent_017_negative_count
        for r in agent_017_records[:needed]:
            r["overall_sentiment"] = "NEGATIVE"
            r["customer_sentiment_score"] = round(np.random.uniform(-5.0, -1.0), 2)
            r["agent_sentiment_score"] = round(np.random.uniform(-3.0, 2.0), 2)

    return records


# ---------------------------------------------------------------------------
# Write Parquet partitioned
# ---------------------------------------------------------------------------
def write_parquet_partitioned(df: pd.DataFrame, output_dir: str, prefix: str):
    """Write DataFrame as Parquet files partitioned by year/month/day."""
    for (year, month, day), group in df.groupby(["year", "month", "day"]):
        part_dir = os.path.join(output_dir, prefix, f"year={year}", f"month={month}", f"day={day}")
        os.makedirs(part_dir, exist_ok=True)
        # Drop partition columns from the data file
        data = group.drop(columns=["year", "month", "day"])
        filepath = os.path.join(part_dir, "data.parquet")
        data.to_parquet(filepath, engine="pyarrow", index=False)


# ---------------------------------------------------------------------------
# Write JSON partitioned
# ---------------------------------------------------------------------------
def write_json_partitioned(records: list[dict], output_dir: str, prefix: str):
    """Write records as JSON files partitioned by year/month/day."""
    from collections import defaultdict

    partitions = defaultdict(list)
    for record in records:
        key = (record["year"], record["month"], record["day"])
        # Remove partition keys from the record written to file
        rec_copy = {k: v for k, v in record.items() if k not in ("year", "month", "day")}
        partitions[key].append(rec_copy)

    for (year, month, day), recs in partitions.items():
        part_dir = os.path.join(output_dir, prefix, f"year={year}", f"month={month}", f"day={day}")
        os.makedirs(part_dir, exist_ok=True)
        filepath = os.path.join(part_dir, "data.json")
        with open(filepath, "w") as f:
            for rec in recs:
                f.write(json.dumps(rec) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Connect analytics data")
    parser.add_argument("--output-dir", default="output", help="Output directory (default: output)")
    args = parser.parse_args()

    output_dir = args.output_dir
    print(f"Generating synthetic data to: {output_dir}/")
    print(f"Seed: {SEED}")
    print()

    # --- CTR Records ---
    print(f"Generating {NUM_CTR:,} CTR records...")
    ctr_df = generate_ctr_records(NUM_CTR)
    write_parquet_partitioned(ctr_df, output_dir, "ctr")
    print(f"  CTR records written. Outcomes: {ctr_df['outcome'].value_counts().to_dict()}")
    print(f"  Mean handle time: {ctr_df[ctr_df['outcome'] == 'CONNECTED']['handle_time_seconds'].mean():.0f}s")
    print()

    # --- Agent Event Records ---
    print(f"Generating {NUM_AGENT_EVENTS:,} Agent Event records...")
    agent_events_df = generate_agent_event_records(NUM_AGENT_EVENTS)
    write_parquet_partitioned(agent_events_df, output_dir, "agent-events")
    print(f"  Agent Event records written. States: {agent_events_df['current_state'].value_counts().to_dict()}")
    burnout_occ = agent_events_df[agent_events_df["agent_id"].isin(BURNOUT_AGENTS)]["occupancy_rate"].mean()
    print(f"  Burnout agents mean occupancy: {burnout_occ:.2%}")
    print()

    # --- Contact Lens Records ---
    print(f"Generating {NUM_CONTACT_LENS:,} Contact Lens records...")
    contact_lens_records = generate_contact_lens_records(NUM_CONTACT_LENS)
    write_json_partitioned(contact_lens_records, output_dir, "contact-lens")
    sentiment_counts = {}
    for r in contact_lens_records:
        s = r["overall_sentiment"]
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
    print(f"  Contact Lens records written. Sentiments: {sentiment_counts}")
    agent_017_neg = sum(1 for r in contact_lens_records if r["agent_id"] == "Agent-017" and r["overall_sentiment"] == "NEGATIVE")
    print(f"  Agent-017 negative calls: {agent_017_neg}")
    print()

    # --- Summary ---
    print("=" * 60)
    print("Generation complete!")
    print(f"  CTR:          {NUM_CTR:>6,} records (Parquet)")
    print(f"  Agent Events: {NUM_AGENT_EVENTS:>6,} records (Parquet)")
    print(f"  Contact Lens: {NUM_CONTACT_LENS:>6,} records (JSON)")
    print(f"  Output dir:   {os.path.abspath(output_dir)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
