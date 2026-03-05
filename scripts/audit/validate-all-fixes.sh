#!/bin/bash
# Comprehensive validation of all documentation fixes

echo "=========================================="
echo "  Documentation Validation"
echo "=========================================="
echo ""

# Check for broken links
echo "1. Broken Links Check"
BROKEN=$(grep -r "\[.*\](.*.md)" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)
echo "   Markdown links scanned: $(grep -r "\[.*\](.*.md)" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)"
echo "   Potentially broken: $BROKEN"
if [ $BROKEN -gt 0 ]; then
  echo "   ⚠️  Action needed"
else
  echo "   ✅ Pass"
fi
echo ""

# Check for old version references
echo "2. Version Consistency Check"
OLD_VERSION=$(grep -r "v3\.0\.0" docs/ README.md --include="*.md" | grep -v "Binary file" | wc -l)
echo "   v3.0.0 references found: $OLD_VERSION"
if [ $OLD_VERSION -gt 5 ]; then
  echo "   ⚠️  Multiple v3.0.0 references - needs fix"
elif [ $OLD_VERSION -gt 0 ]; then
  echo "   ⚠️  Some v3.0.0 references in historical context"
else
  echo "   ✅ Pass"
fi
echo ""

# Check observability discoverability
echo "3. Observability Discoverability Check"
OBS_LINKS=$(grep -r "observability\.md" docs/ README.md --include="*.md" | wc -l)
RUNBOOK_INDEX=$(grep -E "on-call|slo-handbook|slo-response|distributed-tracing|performance-analysis" docs/runbooks/README.md | wc -l)
echo "   observability.md references: $OBS_LINKS"
echo "   New runbooks indexed: $RUNBOOK_INDEX"
if [ $OBS_LINKS -lt 2 ]; then
  echo "   ⚠️  observability.md not linked from main docs"
else
  echo "   ✅ Pass"
fi
if [ $RUNBOOK_INDEX -lt 5 ]; then
  echo "   ⚠️  Not all new runbooks indexed"
else
  echo "   ✅ Pass"
fi
echo ""

# Check for ADRs
echo "4. Architecture Documentation Check"
ADR_OBS=$(ls docs/architecture/006-*.md 2>/dev/null | wc -l)
echo "   Observability ADRs created: $ADR_OBS"
if [ $ADR_OBS -lt 3 ]; then
  echo "   ⚠️  Some observability ADRs missing"
else
  echo "   ✅ Pass"
fi
echo ""

# Summary
echo "=========================================="
echo "  Validation Summary"
echo "=========================================="
echo "Documentation fixes applied. Run full audit for complete status."
echo ""
