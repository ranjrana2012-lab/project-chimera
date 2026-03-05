#!/bin/bash
# Analyze broken links from audit report

echo "Analyzing broken links..."
echo "Total broken links: 170"

# Extract broken links from audit report
grep -E "BROKEN:|broken link" docs/DOCUMENTATION_AUDIT_REPORT.md > /tmp/broken-links-list.txt

echo "Broken links extracted to /tmp/broken-links-list.txt"
wc -l /tmp/broken-links-list.txt
