#!/usr/bin/env bash
# ============================================================================
# Forbidden Flagship Pattern Scanner
#
# Scans production code for hardcoded flagship values that should not appear
# in generic pipeline code. Returns exit code 1 if any violations are found.
#
# ALLOWED locations (test fixtures, demos, mock providers, examples):
#   - tests/
#   - scripts/run_flagship_demo.py
#   - backend/diagnosis_ai/provider.py (mock providers)
#   - backend/translator/provider.py (mock providers)
#   - backend/datasets/registry.py (catalog registration)
#   - backend/analyzer/demo.py
#   - backend/lab/
#   - examples/
#   - backend/diagnosis_ai/cli.py
#
# FORBIDDEN locations (production code):
#   - backend/orchestrator/
#   - backend/api/
#   - backend/assurance/
#   - backend/repair_verification/
#   - backend/validation/validators/
#   - frontend/src/
# ============================================================================

set -euo pipefail

REPO_ROOT="${1:-.}"
VIOLATIONS=0

# Patterns to search for (each line: pattern | description)
PATTERNS=(
  'customer_risk|Hardcoded flagship dataset ID'
  't\.amount > 500|Flagship source expression'
  't\.amount >= 500|Flagship target expression'
  'CUST-00042|Flagship sample row key'
  'CUST-00108|Flagship sample row key'
)

# Forbidden directories (relative to REPO_ROOT)
FORBIDDEN_DIRS=(
  "backend/orchestrator"
  "backend/api"
  "backend/assurance"
  "backend/repair_verification"
  "backend/validation/validators"
  "frontend/src"
)

# Allowed files that may contain patterns legitimately
ALLOWED_FILES=(
  "scripts/run_flagship_demo.py"
  "backend/diagnosis_ai/provider.py"
  "backend/translator/provider.py"
  "backend/datasets/registry.py"
  "backend/analyzer/demo.py"
  "backend/diagnosis_ai/cli.py"
  # Frontend: Flagship example button + constant (explicit user action)
  "frontend/src/pages/NewMigrationPage.tsx"
  # Frontend: Test fixtures
  "frontend/src/test/"
)

echo "=== Forbidden Flagship Pattern Scanner ==="
echo "Repository root: $REPO_ROOT"
echo ""

for pattern_entry in "${PATTERNS[@]}"; do
  IFS='|' read -r pattern description <<< "$pattern_entry"

  for dir in "${FORBIDDEN_DIRS[@]}"; do
    target_path="$REPO_ROOT/$dir"
    if [ ! -d "$target_path" ]; then
      continue
    fi

    # Search for pattern, exclude allowed files
    while IFS= read -r match; do
      # Check if this file is in the allowed list
      is_allowed=false
      for allowed in "${ALLOWED_FILES[@]}"; do
        if [[ "$match" == *"$allowed"* ]]; then
          is_allowed=true
          break
        fi
      done

      if [ "$is_allowed" = false ]; then
        echo "❌ VIOLATION: $description"
        echo "   Pattern: $pattern"
        echo "   $match"
        echo ""
        VIOLATIONS=$((VIOLATIONS + 1))
      fi
    done < <(grep -rn "$pattern" "$target_path" --include="*.py" --include="*.tsx" --include="*.ts" 2>/dev/null || true)
  done
done

echo "=== Scan Complete ==="
if [ $VIOLATIONS -gt 0 ]; then
  echo "❌ Found $VIOLATIONS violation(s). Production code contains hardcoded flagship patterns."
  exit 1
else
  echo "✅ Zero violations. No hardcoded flagship patterns in production code."
  exit 0
fi
