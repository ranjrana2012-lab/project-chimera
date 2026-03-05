# Evaluation Criteria Documentation

**Version:** 1.0
**Last Updated:** March 2026
**Applies to:** All Project Chimera contributions

---

## Overview

This document defines the evaluation criteria used to review contributions to Project Chimera. These criteria ensure code quality, maintainability, and alignment with project goals.

---

## Code Quality Criteria

### 1. Code Style & Formatting

**Requirements:**
- Code passes `black` formatting check
- Code passes `ruff` linting check
- No TODO or FIXME comments in production code
- Line length ≤ 120 characters (hard limit)
- Follows PEP 8 for Python code

**Evaluation:**
```bash
# Check formatting
make format-check  # or: black --check .

# Check linting
make lint        # or: ruff check .

# Check both
make check-style
```

**Acceptance Criteria:**
- ✅ Zero formatting errors
- ✅ Zero linting errors (or explicitly waived)
- ✅ No inline TODOs (convert to GitHub issues)

---

### 2. Testing Standards

**Requirements:**
- New code includes unit tests
- Test coverage maintained or improved
- Tests follow AAA (Arrange-Act-Assert) pattern
- Tests are independent and can run in parallel
- No hardcoded test data (use fixtures)

**Coverage Targets:**
- **Unit Tests:** 80%+ coverage for new code
- **Integration Tests:** Critical paths must be covered
- **E2E Tests:** Main user flows must be covered

**Evaluation:**
```bash
# Run tests with coverage
pytest --cov=services --cov-report=html

# Check coverage threshold
pytest --cov=services --cov-fail-under=80
```

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ New code has 80%+ coverage
- ✅ Overall project coverage not decreased
- ✅ Tests added for new features
- ✅ Tests added for bug fixes

---

### 3. Documentation Standards

**Requirements:**
- All public functions have docstrings
- Complex logic has inline comments
- API changes documented in `docs/api/`
- Architecture decisions documented (if needed)
- README updated for user-facing changes

**Docstring Format:**
```python
def generate_dialogue(prompt: str, adapter: str = "gpt-4") -> DialogueResponse:
    """Generate dialogue from prompt.

    Args:
        prompt: Input prompt for generation
        adapter: LLM adapter to use (default: "gpt-4")

    Returns:
        DialogueResponse with generated text and metadata

    Raises:
        ValueError: If prompt is empty
        GenerationError: If generation fails

    Example:
        >>> generate_dialogue("Hello world", "gpt-4")
        DialogueResponse(text="Hello back!", ...)
    """
```

**Evaluation:**
```bash
# Check docstrings
make docstring-check
```

**Acceptance Criteria:**
- ✅ All new public functions have docstrings
- ✅ Docstrings follow Google style
- ✅ API documentation updated
- ✅ README updated for user-facing changes
- ✅ No outdated documentation

---

## Architecture Criteria

### 4. Design Principles

**Requirements:**
- Single Responsibility Principle followed
- DRY (Don't Repeat Yourself) followed
- YAGNI (You Aren't Gonna Need It) followed
- No circular dependencies
- Services are loosely coupled

**Evaluation Questions:**
- Does this change follow existing patterns?
- Is this code reusable?
- Is this code over-engineered for the requirement?
- Does this introduce tight coupling?

**Acceptance Criteria:**
- ✅ Follows existing architectural patterns
- ✅ No code duplication (extract common logic)
- ✅ Minimal complexity for the requirement
- ✅ No circular imports
- ✅ Services remain independent

---

### 5. Performance Criteria

**Requirements:**
- No significant performance regression
- No memory leaks
- Efficient database queries
- Appropriate caching (when beneficial)
- Resource limits defined (CPU, memory)

**Performance Targets:**
- API response: <100ms (p50), <500ms (p95)
- Dialogue generation: <3s (p50), <5s (p95)
- Caption latency: <500ms
- Database queries: <100ms (p95)

**Evaluation:**
```bash
# Run performance tests
pytest tests/performance/ -v

# Check for memory leaks
pytest tests/load/ --maxfail=1
```

**Acceptance Criteria:**
- ✅ No significant performance regression
- ✅ Memory usage stable over time
- ✅ Database queries optimized
- ✅ Resource limits specified in deployment
- ✅ Performance tests pass

---

## Security Criteria

### 6. Security Standards

**Requirements:**
- No hardcoded credentials
- Input validation on all endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)
- Secrets managed via Kubernetes secrets
- Dependencies scanned for vulnerabilities

**Evaluation:**
```bash
# Scan dependencies
pip-audit

# Check for secrets
git log --all --full-history -S '' -- "**" | grep -i "password\|secret\|key"
```

**Acceptance Criteria:**
- ✅ No hardcoded credentials
- ✅ Input validation on all endpoints
- ✅ No SQL injection vulnerabilities
- ✅ No XSS vulnerabilities
- ✅ Secrets in Kubernetes secrets (not in code)
- ✅ No high-severity vulnerabilities in dependencies

---

## Review Process

### Pre-Submission Checklist

Contributors should verify:
- [ ] Code formatted (`make format`)
- [ ] Code linted (`make lint`)
- [ ] Tests passing (`make test`)
- [ ] Coverage maintained (`pytest --cov`)
- [ ] Docstrings added
- [ ] Documentation updated
- [ ] No secrets committed
- [ ] Performance tested (if relevant)

### Reviewer Checklist

Reviewers evaluate:
- [ ] Code follows style guide
- [ ] Tests are adequate
- [ ] Documentation is complete
- [ ] No security issues
- [ ] Performance is acceptable
- [ ] Architecture is sound
- [ ] No over-engineering

### Approval Criteria

PR is approved when:
- All automated checks pass (CI/CD)
- At least one reviewer approves
- No unresolved blocking concerns
- Code review criteria met

---

## Pull Request Categories

### 1. Bug Fix

**Criteria:**
- Test case added that reproduces bug
- Fix resolves the test case
- No regression in other tests
- Documentation updated if needed

### 2. Feature Implementation

**Criteria:**
- Feature specification documented
- Tests cover the feature
- Documentation updated
- Performance considered
- Security implications considered

### 3. Refactoring

**Criteria:**
- Tests pass before and after
- No behavior changes
- Code is simpler/clearer
- Performance not degraded
- Documentation updated

### 4. Documentation

**Criteria:**
- Information is accurate
- Formatting follows standards
- Links work correctly
- In appropriate location

---

## Grade Levels

### A (Excellent) - Exceeds Expectations
- All criteria met
- Additional tests added beyond requirements
- Exceptional documentation
- Performance optimizations beyond requirements
- Mentors other contributors

### B (Good) - Meets Expectations
- All criteria met
- Adequate tests
- Sufficient documentation
- Acceptable performance

### C (Acceptable) - Minimally Acceptable
- Most criteria met
- Minor issues that don't block merge
- Tests can be added in follow-up
- Documentation can be improved later

### D (Needs Revision) - Below Expectations
- Major criteria not met
- Blocking issues that must be fixed
- Requires significant work
- Must be revised before merge

### F (Rejected) - Unacceptable
- Breaks existing functionality
- Security vulnerabilities
- No tests
- Inappropriate for project

---

## Common Issues & Feedback

### Frequent Issues

1. **Missing Tests**
   - Feedback: "Add tests for new functionality"
   - Action: Add unit/integration tests

2. **Poor Documentation**
   - Feedback: "Add docstrings to public functions"
   - Action: Add comprehensive docstrings

3. **Style Violations**
   - Feedback: "Run `make format` before committing"
   - Action: Format code with black/ruff

4. **Over-Engineering**
   - Feedback: "Simplify implementation - YAGNI"
   - Action: Remove unnecessary abstraction

5. **Performance Regression**
   - Feedback: "This adds 500ms latency"
   - Action: Optimize or add caching

---

## Appeals Process

If you disagree with evaluation feedback:

1. **Discuss with reviewer** - Clarify concerns
2. **Provide justification** - Explain your approach
3. **Compromise when possible** - Find middle ground
4. **Escalate if needed** - Contact technical lead

---

## Related Documentation

- [Development Guide](../DEVELOPMENT.md) - Development workflow
- [Testing Guide](../runbooks/testing-guide.md) - Testing procedures
- [Code Review Process](../CONTRIBUTING.md) - Review process
- [Documentation Contribution Guide](contributing/documentation.md) - Docs standards

---

*Evaluation Criteria Documentation - Project Chimera v0.4.0 - March 2026*
