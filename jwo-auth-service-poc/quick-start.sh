#!/bin/bash

# JWO Auth Service POC - Quick Start Script

set -e

echo "🚀 JWO Prepaid Card Authorization Service - POC"
echo "=============================================="
echo ""

# Check Java
echo "✓ Checking Java installation..."
if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Please install Java 17+"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | grep -oP 'version "\K[0-9]+' | head -1)
if [ "$JAVA_VERSION" -lt 17 ]; then
    echo "❌ Java 17+ required (found: $JAVA_VERSION)"
    exit 1
fi
echo "✓ Java $JAVA_VERSION found"
echo ""

# Check Maven
echo "✓ Checking Maven installation..."
if ! command -v mvn &> /dev/null; then
    echo "❌ Maven not found. Please install Maven 3.8+"
    exit 1
fi
echo "✓ Maven found: $(mvn -v | head -1)"
echo ""

# Build
echo "📦 Building POC..."
mvn clean package -q -DskipTests
echo "✓ Build complete"
echo ""

# Run tests
echo "🧪 Running unit tests..."
mvn test -q
echo "✓ All tests passed!"
echo ""

# Display instructions
echo "✨ POC is ready!"
echo ""
echo "To start the service, run:"
echo "  mvn spring-boot:run"
echo ""
echo "Then test with:"
echo "  curl -X POST http://localhost:8080/api/v1/authorize/check-entry \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"store_id\":\"store-123\",\"card_data\":{\"card_number\":\"4111111111111111\"},\"request_id\":\"req-1\"}'"
echo ""
echo "Documentation: See README.md for full API and testing instructions"
echo ""
