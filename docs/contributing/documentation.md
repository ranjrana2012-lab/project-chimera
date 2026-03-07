# Documentation Contribution Guidelines

**Version:** 1.0
**Last Updated:** March 2026

---

## Overview

This guide covers how to contribute to Project Chimera documentation, including standards, processes, and review criteria.

---

## Documentation Structure

```
docs/
├── api/                    # API documentation for each service
├── architecture/           # Architecture Decision Records (ADRs)
├── contributing/           # Contribution guidelines (this file)
├── getting-started/       # Getting started guides
├── observability.md        # Observability platform overview
├── plans/                  # Implementation plans and designs
├── runbooks/              # Operational procedures
└── services/              # Service documentation
```

---

## Writing Standards

### Markdown Format

- Use GitHub Flavored Markdown (GFM)
- Line length: 100 characters (soft), 120 (hard)
- Use ATX-style headers (`# Header`)

### Code Blocks

- Use triple backticks with language identifier
- For bash: ` ```bash `
- For Python: ` ```python `

### Links

- Use relative links for internal docs: `Text`
- Use absolute links for external resources: `[Text](https://example.com)`
- Link text should be descriptive, not "click here"

### Images/Diagrams

- Store images in `docs/images/`
- Use descriptive alt text
- Prefer ASCII diagrams for simple diagrams

---

## Documentation Types

### API Documentation

When documenting API endpoints:
- Include endpoint path and method
- Document request/response schemas
- Provide example requests and responses
- Document error responses
- Note any authentication required

### Runbooks

When creating operational runbooks:
- Start with problem statement
- Provide step-by-step procedures
- Include verification steps
- Add escalation procedures
- Include "Quick Reference" section

### ADRs

When creating Architecture Decision Records:
- Use existing ADR template format
- Include context, decision, consequences
- Document alternatives considered
- Link to related ADRs

---

## Review Process

### Before Submitting

1. **Run link checker**
   ```bash
   ./scripts/fix/analyze-broken-links.sh
   ```

2. **Check for version consistency**
   - Ensure versions are v0.4.0 (not v3.0.0)
   - Check footers and headers

3. **Preview changes**
   - Use markdown previewer or GitHub preview

### Creating Pull Request

1. **Title:** Use format `docs(area): description`
   - Example: `docs(api): add metrics section to SceneSpeak`

2. **Description:** Include:
   - What changes were made
   - Why they were made
   - Links to related issues

3. **Labels:** Add appropriate labels:
   - `documentation`
   - `component-{area}`

### Review Criteria

Documentation PRs are reviewed for:
- **Accuracy** - Information is correct
- **Clarity** - Easy to understand
- **Completeness** - Covers the topic adequately
- **Consistency** - Matches existing style
- **Links** - No broken links introduced

---

## Testing Documentation

### Link Testing

Before submitting, verify all links work:
```bash
# Check internal links
./scripts/fix/analyze-broken-links.sh

# Check external links (optional)
grep -r "http.*\.md" docs/ | head -20
```

### Example Testing

If you include code examples, test them:
```bash
# For bash examples
bash -c 'example-command'

# For Python examples
python3 -c 'example-code'
```

---

## Common Tasks

### Adding New Runbook

1. Create file in `docs/runbooks/`
2. Use existing runbook as template
3. Add to `docs/runbooks/README.md` index
4. Link from related documentation

### Updating API Documentation

1. Modify service API file in `docs/api/`
2. Test endpoint examples if possible
3. Update table of contents if adding new section

### Creating ADR

1. Copy existing ADR template
2. Number sequentially (next available number)
3. Include all required sections
4. Link from `docs/architecture/README.md`

---

## Getting Help

- **Documentation Issues:** Open issue with `documentation` label
- **Questions:** Ask in `#documentation` channel
- **Review:** Request review from technical documentation lead

---

**See Also:**
- [Main Contributing Guide](../CONTRIBUTING.md)
- [API Documentation](../api/)
- [Runbooks](../runbooks/)
