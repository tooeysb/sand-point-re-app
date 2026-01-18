#!/bin/bash
# =============================================================================
# SETUP GIT HOOKS
# =============================================================================
# Run this script to install the pre-push hook that validates Excel parity
# before Heroku deployments.
#
# Usage:
#   ./scripts/setup-hooks.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "Setting up git hooks..."

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Copy pre-push hook
cat > "$HOOKS_DIR/pre-push" << 'HOOK_CONTENT'
#!/bin/bash
# =============================================================================
# GIT PRE-PUSH HOOK
# =============================================================================
# This hook runs Excel parity tests before pushing to Heroku.
# If tests fail, the push is blocked.
#
# To bypass (DANGEROUS - only for emergencies):
#   git push --no-verify heroku main
# =============================================================================

# Get the remote name being pushed to
remote="$1"

# Only run tests when pushing to heroku
if [[ "$remote" == "heroku" ]]; then
    echo ""
    echo "============================================================"
    echo "  HEROKU DEPLOYMENT DETECTED"
    echo "  Running Excel parity tests before deployment..."
    echo "============================================================"
    echo ""

    # Run the pre-deploy check script
    if [ -f "scripts/pre-deploy-check.sh" ]; then
        bash scripts/pre-deploy-check.sh prod
        EXIT_CODE=$?
    else
        # Fallback: run tests directly
        echo "Running tests directly..."
        TEST_PRODUCTION=1 python tests/test_excel_parity_critical.py
        EXIT_CODE=$?
    fi

    if [ $EXIT_CODE -ne 0 ]; then
        echo ""
        echo "============================================================"
        echo "  PUSH BLOCKED: Excel parity tests failed!"
        echo ""
        echo "  Fix the calculation discrepancies before deploying."
        echo "  To bypass (NOT RECOMMENDED): git push --no-verify heroku main"
        echo "============================================================"
        echo ""
        exit 1
    fi
fi

exit 0
HOOK_CONTENT

chmod +x "$HOOKS_DIR/pre-push"

echo ""
echo "Git hooks installed successfully!"
echo ""
echo "The pre-push hook will now:"
echo "  - Run Excel parity tests before any push to 'heroku' remote"
echo "  - Block deployment if tests fail"
echo ""
echo "To test manually: ./scripts/pre-deploy-check.sh"
echo ""
