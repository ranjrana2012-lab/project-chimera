# Implementation Plan: Dual-Stack NemoClaw/OpenClaw Architecture for Project Chimera

**Date:** 2026-03-30
**Status:** PLANNING
**Complexity:** HIGH
**Estimated Effort:** 20-30 hours

---

## Executive Summary

This plan outlines the implementation of a production-grade dual-stack AI agent deployment for Project Chimera, separating concerns between **Telegram orchestration** (via OpenClaw) and **Discord interaction** (via NemoClaw), while maintaining the existing Chimera microservices infrastructure.

### Key Decision Points

1. **OpenClaw (Telegram)**: Standard Docker Compose deployment for proven orchestration
2. **NemoClaw (Discord)**: Isolated Docker deployment with host-side Discord bridge
3. **Integration Point**: Project Chimera's existing `openclaw-orchestrator` service
4. **Security Model**: Zero-trust VPN via Tailscale, strict iptables hardening

---

## Current State Analysis

### Existing Infrastructure

| Component | Status | Port | Notes |
|-----------|--------|------|-------|
| **openclaw-orchestrator** | ✅ Active | 8000 | FastAPI service |
| **nemoclaw-orchestrator** | ✅ Active | 9000 | Privacy router (Z.AI → Nemotron) |
| **Infrastructure Services** | ✅ Active | Various | Redis, Kafka, Milvus, Prometheus, etc. |
| **Host k3s** | ✅ Running | 6443 | Compatible with DGX Spark ARM64 |
| **Official NemoClaw** | ❌ Incompatible | - | Docker-in-Docker fails on cgroup v2 |

### Key Constraints

1. **DGX Spark Architecture**: ARM64 + Ubuntu 24.04 (cgroup v2)
2. **NemoClaw Limitation**: Official version requires Docker-in-Docker (incompatible)
3. **Working Alternative**: Chimera's custom `nemoclaw-orchestrator` service
4. **Security Requirement**: Zero inbound public ports, VPN-only access

---

## Implementation Plan

### Phase 1: Infrastructure Preparation (4-6 hours)

#### 1.1 Docker Engine Verification & Hardening

**Tasks:**
- [ ] Verify official Docker CE installation (not docker.io or Snap)
- [ ] Configure DOCKER-USER iptables chain to prevent UFW bypass
- [ ] Install `iptables-persistent` for rule persistence
- [ ] Verify Docker daemon configuration for cgroup v2 compatibility

**Commands:**
```bash
# Verify Docker version
docker version

# Check for official Docker CE
dpkg -l | grep docker-ce

# Apply critical security rules
sudo iptables -I DOCKER-USER -i eth0 -j DROP
sudo iptables -I DOCKER-USER -i eth0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo netfilter-persistent save
```

**Acceptance Criteria:**
- [ ] Docker CE (not docker.io) confirmed installed
- [ ] DOCKER-USER iptables rules active and persistent
- [ ] No ports exposed to 0.0.0.0 (all services bind to 127.0.0.1)

---

#### 1.2 Network Isolation Setup

**Tasks:**
- [ ] Create dedicated Docker networks for OpenClaw and NemoClaw zones
- [ ] Configure inter-service communication via Chimera backend network
- [ ] Document network topology and firewall rules

**Network Architecture:**
```
chimera-backend          (existing)  - Chimera microservices
chimera-frontend         (existing)  - External-facing services
chimera-openclaw-zone    (new)       - OpenClaw/Telegram isolation
chimera-nemoclaw-zone    (new)       - NemoClaw/Discord isolation
```

**Commands:**
```bash
# Create isolated networks
docker network create chimera-openclaw-zone --driver bridge --internal
docker network create chimera-nemoclaw-zone --driver bridge --internal
```

**Acceptance Criteria:**
- [ ] Isolated networks created and verified
- [ ] Services can communicate via Chimera backend network
- [ ] No direct internet access from zone networks (proxy-only)

---

### Phase 2: OpenClaw Deployment for Telegram (6-8 hours)

#### 2.1 Directory Structure & Permissions

**Tasks:**
- [ ] Create `/opt/openclaw-chimera` deployment directory
- [ ] Set up config and workspace subdirectories with UID 1000 ownership
- [ ] Configure secure permissions (700 for config, 755 for workspace)

**Commands:**
```bash
sudo mkdir -p /opt/openclaw-chimera/{config,workspace}
sudo chown -R 1000:1000 /opt/openclaw-chimera
sudo chmod 700 /opt/openclaw-chimera/config
```

**Acceptance Criteria:**
- [ ] Directories created with correct ownership
- [ ] No permission errors during container startup

---

#### 2.2 Environment Configuration

**Tasks:**
- [ ] Generate secure OPENCLAW_GATEWAY_TOKEN (48-char random string)
- [ ] Configure TELEGRAM_BOT_TOKEN from @BotFather
- [ ] Pin OpenClaw image version (avoid `latest` tag)
- [ ] Set restrictive security options

**File:** `/opt/openclaw-chimera/.env`
```bash
# Security Token (generate with: openssl rand -hex 24)
OPENCLAW_GATEWAY_TOKEN=YOUR_48_CHAR_SECURE_TOKEN_HERE

# Container Image (pin version)
OPENCLAW_IMAGE=ghcr.io/openclaw/openclaw-gateway:2026.3.24

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE

# Integration with Chimera
CHIMERA_ORCHESTRATOR_URL=http://openclaw-orchestrator:8000
CHIMERA_ENABLE_INTEGRATION=true
```

**Acceptance Criteria:**
- [ ] .env file created with chmod 600 permissions
- [ ] No hardcoded secrets in docker-compose.yml
- [ ] Telegram bot provisioned via @BotFather

---

#### 2.3 Production Docker Compose Configuration

**File:** `/opt/openclaw-chimera/docker-compose.yml`

**Key Security Directives:**
```yaml
services:
  openclaw-gateway:
    image: ${OPENCLAW_IMAGE}
    container_name: chimera-openclaw-telegram
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /var/tmp:noexec,nosuid,size=50m
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    ports:
      - "127.0.0.1:18789:18789"  # Loopback binding only
    networks:
      - chimera-openclaw-zone
      - chimera-backend
    environment:
      - OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - CHIMERA_ORCHESTRATOR_URL=${CHIMERA_ORCHESTRATOR_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18789/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
```

**Acceptance Criteria:**
- [ ] Container starts without errors
- [ ] Healthcheck passes within 60 seconds
- [ ] Dashboard accessible via `127.0.0.1:18789`
- [ ] No ports exposed to public network

---

#### 2.4 Zero-Trust Pairing Configuration

**Tasks:**
- [ ] Configure OpenClaw pairing policy for Telegram
- [ ] Test cryptographic handshake process
- [ ] Document pairing approval workflow

**Configuration:** Add to `/opt/openclaw-chimera/config/openclaw.json`
```json
{
  "telegram": {
    "requireMention": true,
    "pairing": {
      "enabled": true,
      "ttl": 3600,
      "autoApprove": []
    }
  }
}
```

**Acceptance Criteria:**
- [ ] Unknown users receive pairing code (not rejected silently)
- [ ] Admin can approve pairing via CLI command
- [ ] Group chats work with `requireMention: true`

---

### Phase 3: NemoClaw Deployment for Discord (8-12 hours)

#### 3.1 Host-Side Discord Bridge Setup

**Tasks:**
- [ ] Create Discord application in Discord Developer Portal
- [ ] Enable Message Content Intent and Server Members Intent
- [ ] Generate Discord bot token
- [ ] Deploy Node.js bridge script on host (outside any container)

**File:** `/opt/nemoclaw-chimera/discord-bridge.js`
```javascript
/**
 * Host-side Discord Bridge for NemoClaw
 * Bridges Discord WebSocket → NemoClaw sandbox gateway
 *
 * WORKAROUND: OpenShell HTTP CONNECT proxy blocks WebSocket tunneling
 * SOLUTION: Run bridge on host, relay messages to sandbox via HTTP API
 */

const { Client, GatewayIntentBits } = require('discord.js');
const fetch = require('node-fetch');

const DISCORD_BOT_TOKEN = process.env.DISCORD_BOT_TOKEN;
const NEMOCLAW_GATEWAY_URL = process.env.NEMOCLAW_GATEWAY_URL || 'http://localhost:8080';

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers
  ]
});

client.on('ready', () => {
  console.log(`Discord bridge ready as ${client.user.tag}`);
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  // Relay to NemoClaw sandbox
  try {
    const response = await fetch(`${NEMOCLAW_GATEWAY_URL}/api/discord/incoming`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        author: message.author.id,
        content: message.content,
        channel: message.channel.id,
        guild: message.guild.id
      })
    });

    const data = await response.json();

    // Send response back to Discord
    if (data.reply) {
      message.reply(data.reply);
    }
  } catch (error) {
    console.error('Bridge error:', error);
  }
});

client.login(DISCORD_BOT_TOKEN);
```

**Acceptance Criteria:**
- [ ] Discord bot token configured
- [ ] Bridge script runs without errors
- [ ] Messages from Discord are received

---

#### 3.2 NemoClaw Sandbox Configuration

**Critical Note:** Due to DGX Spark incompatibility with official NemoClaw, we will implement a **custom NemoClaw-compatible sandbox** using the existing `nemoclaw-orchestrator` service.

**Tasks:**
- [ ] Extend existing `nemoclaw-orchestrator` with Discord support
- [ ] Implement sandbox-like isolation using Docker security options
- [ ] Configure network policies for Discord CDN access

**File:** `/home/ranj/Project_Chimera/services/nemoclaw-orchestrator/docker-compose.sandbox.yml`

```yaml
services:
  nemoclaw-discord-sandbox:
    build:
      context: ..
      dockerfile: services/nemoclaw-orchestrator/Dockerfile.sandbox
    container_name: chimera-nemoclaw-discord
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
      - /var/tmp:noexec,nosuid,size=50m
      - /sandbox:rw,size=200m  # Isolated writeable directory
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Minimal networking capability
    security_opt:
      - no-new-privileges:true
      - apparmor:docker-default
      - seccomp:seccomp-profile.json
    networks:
      - chimera-nemoclaw-zone
      - chimera-backend
    environment:
      - SERVICE_NAME=nemoclaw-discord
      - SANDBOX_MODE=true
      - DISCORD_BRIDGE_URL=http://discord-bridge:3000
      - INFERENCE_PROXY_URL=http://nemoclaw-orchestrator:9000
    volumes:
      - nemoclaw-sandbox-state:/sandbox
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  discord-bridge:
    build:
      context: ./discord-bridge
      dockerfile: Dockerfile
    container_name: chimera-discord-bridge
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - NEMOCLAW_GATEWAY_URL=http://nemoclaw-discord-sandbox:9000
    networks:
      - chimera-nemoclaw-zone
    restart: unless-stopped
```

**Acceptance Criteria:**
- [ ] Sandbox container starts with isolated filesystem
- [ ] Discord bridge communicates with sandbox
- [ ] No privilege escalation possible

---

#### 3.3 Network Policy Configuration

**Tasks:**
- [ ] Create seccomp profile for system call filtering
- [ ] Configure AppArmor profile for filesystem restrictions
- [ ] Allow Discord CDN access only (strict egress policy)

**File:** `seccomp-profile.json`
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat", "lstat"],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["connect", "sendto", "recvfrom"],
      "action": "SCMP_ACT_ALLOW",
      "args": [
        {
          "index": 0,
          "value": 443,
          "op": "SCMP_CMP_EQ"
        }
      ]
    }
  ]
}
```

**Acceptance Criteria:**
- [ ] Seccomp profile loaded and enforced
- [ ] Network access restricted to HTTPS only
- [ ] Discord CDN domains whitelisted

---

### Phase 4: Integration with Project Chimera (4-6 hours)

#### 4.1 Orchestrator Service Updates

**Tasks:**
- [ ] Update `openclaw-orchestrator` to support Telegram webhooks
- [ ] Add Discord message handling endpoint
- [ ] Implement bidirectional message routing

**Files to Modify:**
```
services/openclaw-orchestrator/main.py
services/openclaw-orchestrator/routes/telegram.py
services/openclaw-orchestrator/routes/discord.py
```

**Acceptance Criteria:**
- [ ] Telegram messages route to orchestrator
- [ ] Discord messages route to orchestrator
- [ ] Responses propagate back to correct platform

---

#### 4.2 Unified Dashboard Access

**Tasks:**
- [ ] Configure Tailscale VPN on host
- [ ] Set up Tailscale on admin devices
- [ ] Create proxy configuration for dashboard access

**Commands:**
```bash
# Install Tailscale on host
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Access OpenClaw dashboard via Tailnet IP
curl http://100.x.x.x:18789/healthz
```

**Acceptance Criteria:**
- [ ] Dashboard accessible via Tailscale IP
- [ ] No public ports exposed
- [ ] MFA enabled on Tailscale

---

### Phase 5: Security Hardening & Verification (4-6 hours)

#### 5.1 Security Audit

**Tasks:**
- [ ] Run OpenClaw security audit: `docker compose exec openclaw-gateway node dist/index.js security audit --deep`
- [ ] Verify NemoClaw sandbox isolation
- [ ] Test iptables DOCKER-USER rules
- [ ] Confirm no ports exposed to public network

**Commands:**
```bash
# Verify firewall rules
sudo iptables -L DOCKER-USER -v -n

# Scan for open ports
sudo nmap -sS -O localhost

# Test Tailscale-only access
curl http://PUBLIC_IP:18789  # Should fail
curl http://TAILNET_IP:18789  # Should succeed
```

**Acceptance Criteria:**
- [ ] Security audit passes
- [ ] No ports accessible from public IP
- [ ] All services accessible only via Tailscale

---

#### 5.2 Backup & State Management

**Tasks:**
- [ ] Configure automated backups for OpenClaw state
- [ ] Set up NemoClaw PVC backups
- [ ] Document restore procedures
- [ ] Implement credential rotation schedule

**Commands:**
```bash
# Backup OpenClaw state
tar -czf /backups/openclaw-$(date +%Y%m%d).tar.gz /opt/openclaw-chimera/config

# Backup NemoClaw state
docker run --rm -v nemoclaw-sandbox-state:/data -v /backups:/backup alpine tar -czf /backup/nemoclaw-$(date +%Y%m%d).tar.gz /data
```

**Acceptance Criteria:**
- [ ] Automated backups scheduled (cron)
- [ ] Backup encryption implemented (GPG)
- [ ] Restore procedure tested and documented

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Official NemoClaw Incompatibility** | HIGH | Use existing nemoclaw-orchestrator service |
| **Docker UFW Bypass** | CRITICAL | DOCKER-USER iptables rules configured |
| **Discord WebSocket Blocking** | MEDIUM | Host-side bridge implemented |
| **Privilege Escalation** | HIGH | Seccomp + AppArmor + drop capabilities |
| **State Loss** | MEDIUM | Automated backups + PVC persistence |
| **Telegram Bot Token Leak** | HIGH | Environment variables only + chmod 600 |

---

## Verification Checklist

### Pre-Deployment
- [ ] Docker CE installed (not docker.io)
- [ ] DOCKER-USER iptables rules applied
- [ ] Tailscale VPN configured
- [ ] Telegram bot provisioned (@BotFather)
- [ ] Discord application created (Developer Portal)

### Post-Deployment
- [ ] OpenClaw container starts without errors
- [ ] NemoClaw sandbox starts without errors
- [ ] Discord bridge connects successfully
- [ ] Telegram pairing works end-to-end
- [ ] Dashboard accessible via Tailscale only
- [ ] Security audit passes
- [ ] No ports exposed to public network
- [ ] Automated backups configured

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Infrastructure | 4-6 hours | None |
| Phase 2: OpenClaw Setup | 6-8 hours | Phase 1 |
| Phase 3: NemoClaw Setup | 8-12 hours | Phase 1 |
| Phase 4: Integration | 4-6 hours | Phases 2, 3 |
| Phase 5: Hardening | 4-6 hours | Phase 4 |
| **Total** | **26-38 hours** | |

---

## Rollback Strategy

### If Official NemoClaw Fails
1. Stop official NemoClaw containers
2. Rely on existing `nemoclaw-orchestrator` service
3. Use host-side Discord bridge only

### If OpenClaw Deployment Fails
1. Revert to previous docker-compose.yml
2. Restore from backup: `/opt/openclaw-chimera/config`
3. Re-run pairing approval process

### Critical Failure
1. Stop all containers: `docker compose -f /opt/openclaw-chimera/docker-compose.yml down`
2. Restore iptables: `iptables-restore < /etc/iptables/rules.v4`
3. Restart Chimera core services only

---

## Success Metrics

1. **Security**: Zero public ports exposed, all access via Tailscale
2. **Reliability**: 99.9% uptime for Telegram/Discord bots
3. **Performance**: <100ms response time for bot commands
4. **Isolation**: OpenClaw and NemoClaw cannot affect each other
5. **Recoverability**: RTO < 15 minutes, RPO < 1 hour

---

## Next Steps

**Awaiting User Confirmation:**
1. Proceed with Phase 1 (Infrastructure Preparation)?
2. Use existing `nemoclaw-orchestrator` or attempt official NemoClaw workaround?
3. Deploy to development environment first or production directly?

**After Confirmation:**
- Begin Phase 1 implementation
- Create detailed implementation scripts
- Set up monitoring and alerting

---

**Document Status:** READY FOR REVIEW
**Last Updated:** 2026-03-30
**Author:** AI Planning Agent
**Review Required:** User confirmation before proceeding
