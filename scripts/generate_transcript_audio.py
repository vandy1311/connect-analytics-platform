#!/usr/bin/env python3
"""Generate synthetic transcript audio clips using Amazon Polly.

Creates short audio snippets simulating contact center call excerpts
for the demo UI sentiment analysis feature.

Usage: python scripts/generate_transcript_audio.py
Requires: AWS credentials configured with Polly access
"""

import os
import boto3

OUTPUT_DIR = "demo_ui/assets/transcripts"

CLIPS = [
    {
        "file": "negative_billing.mp3",
        "voice": "Joanna",
        "text": (
            "I've been on hold for twenty minutes and nobody can tell me "
            "why I was charged twice. This is absolutely unacceptable. "
            "I want to speak to a manager right now."
        ),
    },
    {
        "file": "negative_interruption.mp3",
        "voice": "Matthew",
        "text": (
            "Ma'am, if you could just. Let me. I understand but. "
            "Ma'am I need you to. OK so what I was trying to say is "
            "that the charge was. No, if you would just let me explain."
        ),
    },
    {
        "file": "positive_resolution.mp3",
        "voice": "Joanna",
        "text": (
            "Thank you so much for your patience. I've gone ahead and "
            "reversed both charges and applied a ten dollar credit to "
            "your account. Is there anything else I can help you with today?"
        ),
    },
    {
        "file": "negative_escalation.mp3",
        "voice": "Joey",
        "text": (
            "Look, I've called three times about this same issue. "
            "Every time I get a different answer. Nobody seems to know "
            "what's going on. I'm done. Cancel my account."
        ),
    },
    {
        "file": "agent_coaching_needed.mp3",
        "voice": "Matthew",
        "text": (
            "Yeah so basically your payment didn't go through. "
            "I don't really know why. You could try again I guess. "
            "Or call your bank. Is there anything else?"
        ),
    },
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    polly = boto3.client("polly", region_name="us-east-1")

    for clip in CLIPS:
        print(f"Generating {clip['file']}...")
        try:
            response = polly.synthesize_speech(
                Text=clip["text"],
                OutputFormat="mp3",
                VoiceId=clip["voice"],
                Engine="neural",
            )
            audio = response["AudioStream"].read()
            path = os.path.join(OUTPUT_DIR, clip["file"])
            with open(path, "wb") as f:
                f.write(audio)
            print(f"  Saved {len(audio):,} bytes")
        except Exception as e:
            print(f"  FAILED: {e}")

    print(f"\nDone. Files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
