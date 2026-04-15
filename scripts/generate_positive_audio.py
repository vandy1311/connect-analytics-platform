#!/usr/bin/env python3
"""Generate positive sentiment transcript audio clips using Polly."""

import os
import boto3

OUTPUT_DIR = "demo_ui/assets/transcripts"

CLIPS = [
    {
        "file": "positive_agent008_empathy.mp3",
        "voice": "Joanna",
        "text": (
            "I completely understand how frustrating that must be, and I'm really sorry "
            "you've had to deal with this. Let me take care of it right now. I've already "
            "pulled up your account and I can see exactly what happened. Give me just one "
            "moment and I'll have this sorted out for you."
        ),
    },
    {
        "file": "positive_agent014_resolution.mp3",
        "voice": "Matthew",
        "text": (
            "Great news. I've gone ahead and processed your refund. You should see it back "
            "on your card within two to three business days. I've also added a fifteen dollar "
            "credit to your account as an apology for the inconvenience. Is there anything "
            "else I can help you with today?"
        ),
    },
    {
        "file": "positive_agent003_proactive.mp3",
        "voice": "Joanna",
        "text": (
            "Before we wrap up, I noticed your subscription is coming up for renewal next week. "
            "Based on your usage, you might actually save about twenty dollars a month by switching "
            "to our annual plan. Would you like me to walk you through that?"
        ),
    },
    {
        "file": "positive_agent019_deescalation.mp3",
        "voice": "Matthew",
        "text": (
            "I hear you, and you're absolutely right to be upset about this. If I were in your "
            "shoes, I'd feel the same way. Here's what I'm going to do. I'm going to escalate "
            "this to our priority team and personally follow up with you by end of day tomorrow "
            "to make sure it's resolved. Can I get your preferred callback number?"
        ),
    },
    {
        "file": "positive_agent011_closing.mp3",
        "voice": "Joanna",
        "text": (
            "I'm so glad we could get that resolved for you today. Just to recap, your new "
            "billing cycle starts on the fifteenth, the credit has been applied, and you'll "
            "receive a confirmation email within the hour. Thank you for being such a loyal "
            "customer. Have a wonderful rest of your day."
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
