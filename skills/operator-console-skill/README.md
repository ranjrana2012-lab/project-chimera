# Operator Console Skill

Human oversight interface for alerts, approvals, and system monitoring.

## Inputs

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| action | string | Yes | request_approval, get_dashboard |
| type | string | No | Approval type |
| description | string | No | Request description |
| timeout_seconds | integer | No | Approval timeout |
| metadata | object | No | Additional metadata |

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| id | string | Approval/alert ID |
| status | string | Current status |
| pending_approvals | array | Pending approvals |
| alerts | array | Unacknowledged alerts |

## Configuration

- **Timeout:** 100ms
- **Retry:** 2 attempts
- **Caching:** Disabled
- **Alert Retention:** 24 hours

## Usage Example

```yaml
input:
  action: request_approval
  type: lighting-scene-change
  description: "Scene 2 - Dramatic shift"
  timeout_seconds: 30
```
