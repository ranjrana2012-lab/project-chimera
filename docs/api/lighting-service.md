# Lighting Service API Documentation

**Version:** 3.0.0
**Base URL:** `http://localhost:8005`
**Service:** DMX/sACN lighting control

---

## Endpoints

### 1. Set Lighting

Set lighting values for all fixtures.

**Endpoint:** `POST /v1/lighting/set`

**Request Body:**

```json
{
  "intensity": 0.8,
  "color": {"r": 255, "g": 200, "b": 150},
  "transition": 2.0
}
```

**Response:**

```json
{
  "success": true,
  "fixtures_affected": 12,
  "transition_time": 2.0
}
```

---

### 2. Set Fixture Values

Set values for a specific fixture.

**Endpoint:** `POST /v1/lighting/fixture/{fixture_id}`

**Request Body:**

```json
{
  "intensity": 1.0,
  "color": {"r": 255, "g": 0, "b": 0},
  "pan": 180,
  "tilt": 45
}
```

---

### 3. Get Current State

Get current lighting state.

**Endpoint:** `GET /v1/lighting/state`

**Response:**

```json
{
  "fixtures": [
    {
      "id": "fixture_1",
      "intensity": 0.8,
      "color": {"r": 255, "g": 200, "b": 150}
    }
  ]
}
```

---

### 4. Blackout

Blackout all lighting immediately.

**Endpoint:** `POST /v1/lighting/blackout`

**Request Body:**

```json
{
  "fade_time": 0.5
}
```

---

### 5. Health Check

**Endpoint:** `GET /health/live`

**Response:** `OK`

---

*Last Updated: March 2026*
*Lighting Service v3.0.0*
