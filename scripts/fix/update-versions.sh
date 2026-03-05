#!/bin/bash
# Update version references from v3.0.0 to v0.4.0

echo "Updating version references..."

# Update README.md
sed -i 's/v3\.0\.0/v0.4.0/g' README.md

# Update API documentation files (13 files)
find docs/api -name "*.md" -type f -exec sed -i 's/v3\.0\.0/v0.4.0/g' {} \;

# Update runbooks README
sed -i 's/v3\.0\.0/v0.4.0/g' docs/runbooks/README.md

# Update architecture documentation
find docs/architecture -name "*.md" -type f -exec sed -i 's/v3\.0\.0/v0.4.0/g' {} \;

# Update docs/README.md
sed -i 's/v3\.0\.0/v0.4.0/g' docs/README.md

# Update docs/CONTRIBUTING.md
sed -i 's/v3\.0\.0/v0.4.0/g' docs/CONTRIBUTING.md

echo "Version references updated"
