.PHONY: help
help:
	@echo "Project Chimera - Make Targets"
	@echo ""
	@echo "Observability:"
	@echo "  make silence-alerts    - Silence AlertManager alerts for maintenance"

.PHONY: silence-alerts
silence-alerts:
	./scripts/silence-alerts.sh $(DURATION) $(COMMENT) $(MATCHERS)
