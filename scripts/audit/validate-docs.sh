#!/bin/bash
# Validate documentation fixes

echo "=== Validating Documentation Fixes ==="

# Check for remaining broken links
echo "1. Checking for broken links..."
BROKEN=$(grep -r "\[.*\](.*.md)" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)
echo "   Markdown links found: $BROKEN"

# Check for v3.0.0 references
echo "2. Checking for old version references..."
OLD_VERSION=$(grep -r "v3\.0\.0" docs/ README.md --include="*.md" | grep -v "Binary file" | grep -v "DOCUMENTATION_AUDIT_REPORT" | wc -l)
echo "   v3.0.0 references found (excluding audit report): $OLD_VERSION"

# Check for observability.md links
echo "3. Checking observability discoverability..."
OBS_LINKS=$(grep -r "observability\.md" docs/ README.md --include="*.md" | wc -l)
echo "   observability.md references: $OBS_LINKS"

echo "=== Validation Complete ==="
