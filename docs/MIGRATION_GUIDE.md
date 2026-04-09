# Project Chimera Phase 2 - Migration and Upgrade Guide

**Version:** 1.0.0
**Last Updated:** April 9, 2026
**Target Audience:** Developers, System Administrators, Technical Leads

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1 to Phase 2 Migration](#phase-1-to-phase-2-migration)
3. [Service Upgrade Procedures](#service-upgrade-procedures)
4. [Breaking Changes](#breaking-changes)
5. [Data Migration](#data-migration)
6. [Configuration Migration](#configuration-migration)
7. [Rollback Procedures](#rollback-procedures)
8. [Version Compatibility](#version-compatibility)

---

## Overview

This guide provides detailed instructions for migrating from Phase 1 to Phase 2, upgrading services, and handling breaking changes in Project Chimera.

### Migration Paths

1. **Phase 1 → Phase 2**: Add hardware integration services
2. **Phase 2.x → Phase 2.y**: Upgrade within Phase 2
3. **Development → Production**: Deploy to production environment

### Key Principles

- **Backward Compatibility**: Maintain Phase 1 functionality
- **Incremental Migration**: Migrate gradually, test thoroughly
- **Zero Downtime**: Use rolling updates where possible
- **Data Safety**: Always backup before migrating

---

## Phase 1 to Phase 2 Migration

### Migration Overview

Phase 1 (Chimera Core) → Phase 2 (Hardware Integration)

**What Changes:**
- Add DMX Controller service (port 8001)
- Add Audio Controller service (port 8002)
- Add BSL Avatar service (port 8003)
- Update Chimera Core to communicate with new services
- Add monitoring and alerting

**What Stays The Same:**
- Chimera Core adaptive logic
- Sentiment analysis
- Dialogue generation
- Configuration file format

### Pre-Migration Checklist

- [ ] Review Phase 2 architecture
- [ ] Complete Phase 2 planning documents
- [ ] Set up Phase 2 infrastructure
- [ ] Backup Phase 1 data and configuration
- [ ] Test Phase 2 services in isolation
- [ ] Plan migration timeline
- [ ] Prepare rollback plan

### Step-by-Step Migration

#### Step 1: Prepare Infrastructure

```bash
# 1. Create Phase 2 directory structure
mkdir -p services/{dmx-controller,audio-controller,bsl-avatar-service}

# 2. Install Phase 2 dependencies
pip install -e ".[phase2]"

# 3. Verify installation
python -c "from services.dmx_controller import DMXController; print('DMX OK')"
python -c "from services.audio_controller import AudioController; print('Audio OK')"
python -c "from services.bsl_avatar_service import BSLAvatarService; print('BSL OK')"
```

#### Step 2: Deploy Phase 2 Services

```bash
# 1. Start Phase 2 services
docker-compose -f services/docker-compose.phase2.yml up -d

# 2. Verify service health
./scripts/health-check.sh --service all

# 3. Test individual services
curl http://localhost:8001/health  # DMX
curl http://localhost:8002/health  # Audio
curl http://localhost:8003/health  # BSL
```

#### Step 3: Update Chimera Core

**Option A: Use Integration Library**

```python
# In chimera_core.py, add Phase 2 integration

from examples.integration.integration_examples import ShowOrchestrator

class ChimeraCore:
    def __init__(self):
        # Existing Phase 1 initialization
        self.sentiment_analyzer = SentimentAnalyzer()
        self.dialogue_generator = DialogueGenerator()

        # New Phase 2 integration
        self.orchestrator = ShowOrchestrator()
        self.orchestrator.start_show()

    def process_audience_input(self, text: str):
        # Existing Phase 1 processing
        sentiment = self.sentiment_analyzer.analyze(text)
        response = self.dialogue_generator.generate(text, sentiment)

        # New Phase 2 hardware control
        self.orchestrator.update_sentiment(sentiment)
        self.orchestrator.execute_adaptive_scene()
        self.orchestrator.execute_adaptive_audio()
        self.orchestrator.execute_bsl_translation(response)

        return response
```

**Option B: Direct API Calls**

```python
# Make direct HTTP calls to Phase 2 services

import requests

class ChimeraCore:
    def __init__(self):
        # Phase 1 initialization
        self.sentiment_analyzer = SentimentAnalyzer()
        self.dialogue_generator = DialogueGenerator()

        # Phase 2 service URLs
        self.dmx_url = "http://localhost:8001"
        self.audio_url = "http://localhost:8002"
        self.bsl_url = "http://localhost:8003"

    def trigger_scene(self, sentiment_level: str):
        # Trigger appropriate lighting scene
        scene_map = {
            "very_negative": "somber_scene",
            "negative": "tense_scene",
            "neutral": "neutral_scene",
            "positive": "bright_scene",
            "very_positive": "celebration_scene",
        }

        scene = scene_map.get(sentiment_level, "neutral_scene")

        requests.post(f"{self.dmx_url}/api/scenes/{scene}/activate")

    def display_bsl(self, text: str):
        # Translate and display BSL
        requests.post(f"{self.bsl_url}/api/translate", json={"text": text})
```

#### Step 4: Test Integration

```bash
# Run integration tests
pytest tests/integration/test_phase2_integration.py -v

# Run example integration
python examples/integration/integration_examples.py --example basic
```

#### Step 5: Cutover to Phase 2

Once testing is complete:

1. **Update documentation** to reflect Phase 2 capabilities
2. **Train operators** on new hardware controls
3. **Update runbooks** with Phase 2 procedures
4. **Monitor** Phase 2 service performance

---

## Service Upgrade Procedures

### Upgrading Individual Services

**When to Upgrade:**
- New features needed
- Bug fixes released
- Security vulnerabilities patched
- Performance improvements available

### Upgrade Steps

#### 1. Preparation

```bash
# 1. Backup current deployment
./scripts/backup.sh --type full

# 2. Pull latest code
git pull origin main

# 3. Check for breaking changes
git log HEAD~5..HEAD --oneline
```

#### 2. Test Upgrade in Staging

```bash
# 1. Deploy to staging environment
./scripts/deploy.sh --env staging --service dmx --dry-run

# 2. Run tests in staging
pytest tests/integration/test_phase2_integration.py -v

# 3. Run performance benchmarks
python tests/performance/benchmark_phase2.py --service dmx
```

#### 3. Production Upgrade

```bash
# 1. Run health checks before upgrade
./scripts/health-check.sh --service dmx

# 2. Deploy new version
./scripts/deploy.sh --env production --service dmx

# 3. Verify upgrade
./scripts/health-check.sh --service dmx

# 4. Monitor for issues
./scripts/health-check.sh --service dmx --watch
```

### Rolling Updates

For zero-downtime upgrades:

```bash
# 1. Build new version
./scripts/dev-tools.sh --action build --service dmx

# 2. Start new version alongside old
docker-compose -f services/docker-compose.phase2.yml up -d dmx-controller-v2

# 3. Switch traffic to new version
# (Load balancer reconfiguration)

# 4. Stop old version
docker-compose -f services/docker-compose.phase2.yml stop dmx-controller

# 5. Clean up old container
docker-compose -f services/docker-compose.phase2.yml rm -f dmx-controller
```

---

## Breaking Changes

### Version 2.0.0 → 2.1.0

**DMX Controller:**
- **Change**: `channel` parameter renamed to `channel_number`
- **Migration**: Update API calls to use `channel_number`
- **Compatibility**: Use API version header `X-API-Version: 2.1.0`

**Audio Controller:**
- **Change**: Volume range changed from -60 to 0 dB to -60 to -6 dB
- **Migration**: Update volume setpoints above -6 dB
- **Compatibility**: Service will clamp values to -6 dB max

**BSL Avatar Service:**
- **Change**: Translation response format changed
- **Migration**: Update response parsing code
- **Compatibility**: Old format supported until 2.2.0

### Handling Breaking Changes

**Option 1: Update Code**

```python
# Old code (2.0.0)
response = requests.post(
    f"{dmx_url}/api/fixtures/mh_1/channels",
    json={"channel": 1, "value": 255}
)

# New code (2.1.0)
response = requests.post(
    f"{dmx_url}/api/fixtures/mh_1/channels",
    json={"channel_number": 1, "value": 255},
    headers={"X-API-Version": "2.1.0"}
)
```

**Option 2: Use Compatibility Layer**

```python
# Compatibility wrapper
class DMXClientCompat:
    def __init__(self, base_url, version="2.1.0"):
        self.base_url = base_url
        self.version = version

    def set_channel(self, fixture_id, channel, value):
        # Convert old API to new API
        payload = {"channel_number": channel, "value": value}

        headers = {}
        if self.version >= "2.1.0":
            headers["X-API-Version"] = self.version

        response = requests.post(
            f"{self.base_url}/api/fixtures/{fixture_id}/channels",
            json=payload,
            headers=headers
        )
        return response
```

---

## Data Migration

### Configuration Migration

**Phase 1 Configuration:**
```python
# config/phase1.yaml
chimera:
  sentiment_threshold: 0.5
  adaptive_mode: true
```

**Phase 2 Configuration:**
```python
# config/phase2.yaml
chimera:
  sentiment_threshold: 0.5
  adaptive_mode: true

  # New Phase 2 settings
  hardware_integration:
    dmx:
      enabled: true
      universe: 1
      refresh_rate: 44
    audio:
      enabled: true
      max_volume_db: -6
    bsl:
      enabled: true
      gesture_library_path: /data/gestures.json
```

### Migration Script

```python
#!/usr/bin/env python3
"""
Migrate Phase 1 configuration to Phase 2 format.
"""

import yaml
import shutil
from pathlib import Path

def migrate_config(old_config_path: Path, new_config_path: Path):
    """Migrate configuration file."""

    # Load old config
    with open(old_config_path) as f:
        old_config = yaml.safe_load(f)

    # Create new config structure
    new_config = {
        **old_config,
        "hardware_integration": {
            "dmx": {
                "enabled": True,
                "universe": 1,
                "refresh_rate": 44,
            },
            "audio": {
                "enabled": True,
                "max_volume_db": -6,
            },
            "bsl": {
                "enabled": True,
                "gesture_library_path": "/opt/chimera/data/gestures.json",
            },
        },
    }

    # Write new config
    with open(new_config_path, "w") as f:
        yaml.dump(new_config, f, default_flow_style=False)

    # Backup old config
    shutil.copy(old_config_path, f"{old_config_path}.backup")

    print(f"Configuration migrated: {old_config_path} → {new_config_path}")

if __name__ == "__main__":
    migrate_config(
        Path("config/phase1.yaml"),
        Path("config/phase2.yaml")
    )
```

### Gesture Library Migration

If upgrading BSL gesture library:

```bash
# 1. Backup existing library
cp services/bsl-avatar-service/data/gestures.json \
   services/bsl-avatar-service/data/gestures.json.backup

# 2. Convert to new format if needed
python scripts/migrate_gestures.py

# 3. Verify migration
python -c "
import json
with open('services/bsl-avatar-service/data/gestures.json') as f:
    gestures = json.load(f)
print(f'Gestures loaded: {len(gestures)}')
"
```

---

## Configuration Migration

### Environment Variables

**Phase 1 Variables:**
```bash
CHIMERA_SENTIMENT_MODEL=distilbert
CHIMERA_DIALOGUE_MODEL=glm-4.7
```

**Phase 2 Variables:**
```bash
# Phase 1 variables (still needed)
CHIMERA_SENTIMENT_MODEL=distilbert
CHIMERA_DIALOGUE_MODEL=glm-4.7

# New Phase 2 variables
DMX_UNIVERSE=1
DMX_REFRESH_RATE=44
AUDIO_MAX_VOLUME_DB=-6
GESTURE_LIBRARY_PATH=/opt/chimera/data/gestures.json
```

### Migration Script for Environment

```bash
#!/bin/bash
# Migrate environment variables from Phase 1 to Phase 2

# Backup existing .env
cp .env .env.phase1_backup

# Add Phase 2 variables
cat >> .env << 'EOF'

# Phase 2 Hardware Integration
DMX_UNIVERSE=1
DMX_REFRESH_RATE=44
DMX_INTERFACE=/dev/ttyUSB0
AUDIO_MAX_VOLUME_DB=-6
AUDIO_SAMPLE_RATE=48000
GESTURE_LIBRARY_PATH=/opt/chimera/data/gestures.json
EOF

echo "Environment variables migrated"
```

---

## Rollback Procedures

### Service Rollback

**When to Rollback:**
- New version has critical bugs
- Performance degradation
- Breaking changes cause failures
- Security issues discovered

### Immediate Rollback

```bash
# 1. Stop affected service
./scripts/dev-tools.sh --action stop --service dmx

# 2. Restore previous version from backup
./scripts/backup.sh --restore backup_YYYYMMDD_HHMMSS

# 3. Restart service
./scripts/dev-tools.sh --action start --service dmx

# 4. Verify rollback
./scripts/health-check.sh --service dmx
```

### Automated Rollback Script

```bash
#!/bin/bash
# Automated rollback script

SERVICE="${1:-dmx}"
BACKUP_NAME="${2:-}"

if [[ -z "$BACKUP_NAME" ]]; then
    # Find latest backup
    BACKUP_NAME=$(ls -t backups/backup_* | head -1)
    BACKUP_NAME=$(basename "$BACKUP_NAME")
fi

echo "Rolling back $SERVICE to $BACKUP_NAME"

# Stop service
docker-compose -f services/docker-compose.phase2.yml stop "${SERVICE}-controller"

# Restore backup
./scripts/backup.sh --restore "$BACKUP_NAME"

# Restart service
docker-compose -f services/docker-compose.phase2.yml start "${SERVICE}-controller"

# Verify rollback
sleep 5
if curl -sf "http://localhost:8001/health"; then
    echo "✅ Rollback successful"
else
    echo "❌ Rollback failed - manual intervention required"
    exit 1
fi
```

### Full System Rollback

```bash
# 1. Stop all Phase 2 services
docker-compose -f services/docker-compose.phase2.yml down

# 2. Restore complete backup
./scripts/backup.sh --restore backup_YYYYMMDD_HHMMSS

# 3. Restart all services
docker-compose -f services/docker-compose.phase2.yml up -d

# 4. Verify all services
./scripts/health-check.sh --service all
```

---

## Version Compatibility

### Service Compatibility Matrix

| Service Version | Chimera Core | API Version | Notes |
|-----------------|--------------|-------------|-------|
| DMX 2.0.x | Phase 1 | v1 | Initial release |
| DMX 2.1.0 | Phase 1+ | v2 | Breaking changes |
| Audio 2.0.x | Phase 1 | v1 | Initial release |
| Audio 2.1.0 | Phase 1+ | v2 | Volume limit change |
| BSL 2.0.x | Phase 1 | v1 | Initial release |
| BSL 2.1.0 | Phase 1+ | v2 | Response format change |

### Dependency Versions

**Required Python Version:**
- Minimum: 3.12
- Recommended: 3.12 or 3.13

**Key Dependencies:**
- FastAPI: >=0.100.0
- uvicorn: >=0.20.0
- pydantic: >=2.0.0
- prometheus-client: >=0.15.0

### Checking Compatibility

```bash
# Check Python version
python --version

# Check dependency versions
pip list | grep -E "fastapi|uvicorn|pydantic"

# Test compatibility
python tests/integration/test_phase2_integration.py -v
```

---

## Best Practices

### Before Upgrading

1. **Review Release Notes**
   ```bash
   git log v2.0.0..HEAD --oneline
   git show HEAD:docs/RELEASE_NOTES.md
   ```

2. **Test in Development**
   ```bash
   # Create test branch
   git checkout -b test-upgrade

   # Pull changes
   git pull origin main

   # Run tests
   pytest tests/ -v
   ```

3. **Backup Production**
   ```bash
   ./scripts/backup.sh --type full --encrypt
   ```

### During Upgrade

1. **Use Blue-Green Deployment**
   - Deploy new version alongside old
   - Test new version thoroughly
   - Switch traffic when confident

2. **Monitor Closely**
   ```bash
   # Watch logs
   docker-compose -f services/docker-compose.phase2.yml logs -f

   # Monitor health
   ./scripts/health-check.sh --service all --watch
   ```

3. **Have Rollback Ready**
   - Know which backup to restore
   - Test rollback procedure
   - Document rollback decision point

### After Upgrade

1. **Verify Functionality**
   ```bash
   # Run smoke tests
   python examples/integration/integration_examples.py --example basic

   # Run full test suite
   pytest tests/ -v
   ```

2. **Monitor Performance**
   ```bash
   # Run benchmarks
   python tests/performance/benchmark_phase2.py --service all
   ```

3. **Update Documentation**
   - Update version numbers in docs
   - Document any new features
   - Update runbooks if needed

---

## Troubleshooting Migrations

### Common Issues

**Issue: Service won't start after upgrade**

**Diagnosis:**
```bash
# Check logs
docker-compose -f services/docker-compose.phase2.yml logs <service>

# Check for configuration errors
docker-compose -f services/docker-compose.phase2.yml config <service>
```

**Solutions:**
1. Verify environment variables
2. Check for missing dependencies
3. Validate configuration files
4. Rollback if needed

**Issue: API calls failing after upgrade**

**Diagnosis:**
```bash
# Check API version compatibility
curl -H "X-API-Version: 2.1.0" http://localhost:8001/api/status
```

**Solutions:**
1. Update API version headers
2. Use compatibility layer
3. Update request/response parsing

**Issue: Performance degraded after upgrade**

**Diagnosis:**
```bash
# Run performance benchmarks
python tests/performance/benchmark_phase2.py --service all
```

**Solutions:**
1. Check resource usage
2. Review code changes
3. Optimize configuration
4. Rollback if severe

---

## Getting Help

### Resources

- **Troubleshooting Guide**: `docs/TROUBLESHOOTING_GUIDE.md`
- **Developer Guide**: `docs/DEVELOPER_ONBOARDING_GUIDE.md`
- **API Documentation**: `docs/PHASE2_API_EXAMPLES.md`
- **Deployment Guide**: `docs/DEPLOYMENT_AND_OPERATIONS_GUIDE.md`

### Support

If you encounter issues not covered in this guide:

1. Check service logs
2. Run diagnostics: `./scripts/diagnose.sh`
3. Review troubleshooting guide
4. Search existing issues
5. Create new issue with details

---

**Document Version:** 1.0.0
**Last Updated:** April 9, 2026

**Next Review:** When releasing Phase 2.1.0

**Owner:** Project Chimera Development Team
**Approvers:** Technical Lead, DevOps Lead
