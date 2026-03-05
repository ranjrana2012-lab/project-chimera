#!/bin/bash
# Fix broken documentation links

echo "Fixing broken links..."

# Fix reference/architecture.md → docs/reference/architecture.md
find docs -name "*.md" -type f -exec sed -i 's|reference/architecture\.md|docs/reference/architecture.md|g' {} \;

# Fix docs/reference/api.md → docs/api/README.md
find docs -name "*.md" -type f -exec sed -i 's|docs/reference/api\.md|docs/api/README.md|g' {} \;

# Fix docs/runbooks/deployment.md → docs/runbooks/README.md#deployment
find docs -name "*.md" -type f -exec sed -i 's|docs/runbooks/deployment\.md|docs/runbooks/README.md#deployment|g' {} \;

# Fix guides/github-workflow.md → docs/contributing/github-workflow.md
find docs -name "*.md" -type f -exec sed -i 's|guides/github-workflow\.md|docs/contributing/github-workflow.md|g' {} \;

echo "Link fixes applied"
