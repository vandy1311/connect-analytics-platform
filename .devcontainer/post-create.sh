#!/bin/bash
set -e

echo "=== Connect Analytics Platform — Dev Container Setup ==="

# Install Python deps (in case image cache is stale)
pip install -r requirements-dev.txt

# Generate synthetic data
echo "Generating synthetic demo data..."
python scripts/generate_synthetic_data.py --output-dir output

# Run tests to verify everything works
echo "Running test suite..."
python -m pytest tests/ -q

echo ""
echo "=== Setup complete ==="
echo "  Python:    $(python --version)"
echo "  CDK:       $(cdk --version)"
echo "  Graphviz:  $(dot -V 2>&1)"
echo "  Tests:     passed"
echo ""
echo "Quick start:"
echo "  pytest tests/                    # run all tests"
echo "  cdk synth                        # synthesize CloudFormation"
echo "  cdk deploy --all                 # deploy to AWS"
echo "  python scripts/generate_synthetic_data.py  # regenerate data"
echo "=========================================="
