#!/bin/bash
################################################################################
# YouTube Transcript Exporter - Production Readiness Validator
################################################################################

set +e  # Don't exit on individual check failures

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  YouTube Transcript Exporter - Production Readiness Validation     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

passed=0
failed=0

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check() {
    local name="$1"
    shift
    
    if "$@" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $name"
        ((failed++))
    fi
}

# ============================================================================
# Section 1: Python & Dependencies
# ============================================================================
echo "1️⃣  PYTHON & DEPENDENCIES"
echo "──────────────────────────────────────────────────────────────────────"

check "Python 3.9+" python3 --version
check "Git installed" git --version

# ============================================================================
# Section 2: Documentation
# ============================================================================
echo ""
echo "2️⃣  DOCUMENTATION"
echo "──────────────────────────────────────────────────────────────────────"

check "README.md" test -f README.md
check "QUICKSTART.md" test -f QUICKSTART.md
check "INSTALL.md" test -f INSTALL.md
check "API.md" test -f API.md
check "TROUBLESHOOTING.md" test -f TROUBLESHOOTING.md
check "PRODUCTION_READINESS.md" test -f PRODUCTION_READINESS.md

# ============================================================================
# Section 3: Configuration
# ============================================================================
echo ""
echo "3️⃣  CONFIGURATION & SECRETS"
echo "──────────────────────────────────────────────────────────────────────"

check "config.json" test -f config.json
check ".env.example" test -f .env.example
check "requirements.txt" test -f requirements.txt

# ============================================================================
# Section 4: Infrastructure
# ============================================================================
echo ""
echo "4️⃣  CONTAINERIZATION"
echo "──────────────────────────────────────────────────────────────────────"

check "Dockerfile" test -f Dockerfile
check "docker-compose.yml" test -f docker-compose.yml

# ============================================================================
# Section 5: Testing
# ============================================================================
echo ""
echo "5️⃣  TESTING"
echo "──────────────────────────────────────────────────────────────────────"

check "Test suite" test -f tests/test_all.py
check "Tests passing" python3 tests/test_all.py

# ============================================================================
# Section 6: Core
# ============================================================================
echo ""
echo "6️⃣  CORE FUNCTIONALITY"
echo "──────────────────────────────────────────────────────────────────────"

check "system_health_check.py" test -f system_health_check.py
check "export.sh" test -f export.sh
check "download_parallel.sh" test -f download_parallel.sh
check "Database exists" test -f db/canonical.json
check "Required dirs" test -d logs && test -d markdown

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║ SUMMARY"
echo "╚════════════════════════════════════���═══════════════════════════════╝"

total=$((passed + failed))
echo ""
echo "Passed:  ${GREEN}$passed/$total${NC}"
echo "Failed:  ${RED}$failed/$total${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ SYSTEM IS PRODUCTION READY!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Read QUICKSTART.md"
    echo "2. Run: python3 system_health_check.py"
    echo "3. Deploy with confidence!"
    exit 0
else
    echo -e "${RED}⚠️  Some checks failed${NC}"
    exit 1
fi
