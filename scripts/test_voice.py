#!/usr/bin/env python3
"""Quick test script for Nova Sonic voice synthesis.

Prerequisites:
  1. AWS credentials configured (aws configure)
  2. Nova Sonic model access enabled in Bedrock console (us-east-1)
  3. pip install boto3

Usage:
  python scripts/test_voice.py
  python scripts/test_voice.py --text "Your custom text here"
  python scripts/test_voice.py --fallback-polly   # Use Polly if Nova Sonic unavailable
"""

import argparse
import json
import os
import sys
import time


def test_nova_sonic(text: str) -> bytes | None:
    """Test Nova Sonic speech synthesis via Bedrock."""
    import boto3

    print(f"Testing Nova Sonic on Bedrock...")
    print(f"Text: {text[:80]}...")

    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    start = time.monotonic()
    try:
        response = client.invoke_model(
            modelId="amazon.nova-sonic-v1:0",
            contentType="application/json",
            accept="audio/mpeg",
            body=json.dumps({
                "inputText": text,
                "voiceConfig": {"engine": "neural", "languageCode": "en-US"},
            }),
        )
        audio = response["body"].read()
        elapsed = time.monotonic() - start

        print(f"  Nova Sonic OK — {len(audio):,} bytes in {elapsed:.2f}s")
        return audio

    except Exception as e:
        elapsed = time.monotonic() - start
        print(f"  Nova Sonic FAILED after {elapsed:.2f}s: {e}")
        return None


def test_polly_fallback(text: str) -> bytes | None:
    """Fallback: test Polly neural voice."""
    import boto3

    print(f"Testing Polly (fallback)...")

    client = boto3.client("polly", region_name="us-east-1")

    start = time.monotonic()
    try:
        response = client.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId="Matthew",
            Engine="neural",
        )
        audio = response["AudioStream"].read()
        elapsed = time.monotonic() - start

        print(f"  Polly OK — {len(audio):,} bytes in {elapsed:.2f}s")
        return audio

    except Exception as e:
        elapsed = time.monotonic() - start
        print(f"  Polly FAILED after {elapsed:.2f}s: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Test voice synthesis")
    parser.add_argument(
        "--text",
        default="Billing queue at 12 minute average wait. SLA breach detected. 3 agents available, abandonment at 14 percent. Recommend pulling 2 agents from Technical queue.",
    )
    parser.add_argument("--fallback-polly", action="store_true", help="Try Polly if Nova Sonic fails")
    parser.add_argument("--output", default="test_voice.mp3", help="Output file path")
    args = parser.parse_args()

    audio = test_nova_sonic(args.text)

    if audio is None and args.fallback_polly:
        audio = test_polly_fallback(args.text)

    if audio is None:
        print("\nNo audio generated. Check AWS credentials and model access.")
        sys.exit(1)

    with open(args.output, "wb") as f:
        f.write(audio)

    print(f"\nSaved to {args.output} ({len(audio):,} bytes)")
    print(f"Play it: open {args.output}")

    # Auto-play on macOS
    if sys.platform == "darwin":
        os.system(f"open {args.output}")


if __name__ == "__main__":
    main()
