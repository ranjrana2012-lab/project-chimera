#!/bin/bash
# Test script for lighting API endpoints
# Run this after restarting the lighting-sound-music service

set -e

BASE_URL="http://localhost:8005"

echo "Testing Lighting Control API Endpoints"
echo "======================================"
echo ""

# Test 1: Health endpoint with DMX info
echo "1. Testing /health endpoint..."
curl -s "$BASE_URL/health" | grep -q "dmx_info" && echo "   ✅ Health endpoint includes DMX info" || echo "   ❌ Health endpoint missing DMX info"
echo ""

# Test 2: Set lighting scene
echo "2. Testing POST /api/lighting..."
response=$(curl -s -X POST "$BASE_URL/api/lighting" -H "Content-Type: application/json" -d '{"scene": "act1_scene1", "mood": "dramatic"}')
echo "$response" | grep -q '"success":true' && echo "   ✅ Set lighting scene works" || echo "   ❌ Set lighting scene failed"
echo ""

# Test 3: Set lighting color
echo "3. Testing POST /api/lighting/color..."
response=$(curl -s -X POST "$BASE_URL/api/lighting/color" -H "Content-Type: application/json" -d '{"color": "#FF5733", "intensity": 0.8}')
echo "$response" | grep -q '"applied":true' && echo "   ✅ Set lighting color works" || echo "   ❌ Set lighting color failed"
echo ""

# Test 4: Invalid color format (should return 422)
echo "4. Testing POST /api/lighting/color with invalid color..."
status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/lighting/color" -H "Content-Type: application/json" -d '{"color": "invalid-color", "intensity": 0.5}')
[ "$status" = "422" ] && echo "   ✅ Invalid color format rejected (422)" || echo "   ❌ Invalid color format not rejected (got $status)"
echo ""

# Test 5: Set lighting intensity
echo "5. Testing POST /api/lighting/intensity..."
response=$(curl -s -X POST "$BASE_URL/api/lighting/intensity" -H "Content-Type: application/json" -d '{"intensity": 0.5}')
echo "$response" | grep -q '"applied":true' && echo "   ✅ Set lighting intensity works" || echo "   ❌ Set lighting intensity failed"
echo ""

# Test 6: Invalid intensity (should return 422)
echo "6. Testing POST /api/lighting/intensity with invalid value..."
status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/lighting/intensity" -H "Content-Type: application/json" -d '{"intensity": 1.5}')
[ "$status" = "422" ] && echo "   ✅ Invalid intensity rejected (422)" || echo "   ❌ Invalid intensity not rejected (got $status)"
echo ""

# Test 7: Get lighting state
echo "7. Testing GET /api/lighting/state..."
curl -s "$BASE_URL/api/lighting/state" | grep -q "color" && echo "   ✅ Get lighting state works" || echo "   ❌ Get lighting state failed"
echo ""

# Test 8: Get presets
echo "8. Testing GET /api/lighting/presets..."
curl -s "$BASE_URL/api/lighting/presets" | grep -q "presets" && echo "   ✅ Get lighting presets works" || echo "   ❌ Get lighting presets failed"
echo ""

# Test 9: Apply preset
echo "9. Testing POST /api/lighting/preset..."
response=$(curl -s -X POST "$BASE_URL/api/lighting/preset" -H "Content-Type: application/json" -d '{"preset": "dramatic_spotlight"}')
echo "$response" | grep -q '"applied":true' && echo "   ✅ Apply preset works" || echo "   ❌ Apply preset failed (or preset not found)"
echo ""

# Test 10: Zone-specific control
echo "10. Testing POST /api/lighting/zone..."
response=$(curl -s -X POST "$BASE_URL/api/lighting/zone" -H "Content-Type: application/json" -d '{"zone": "stage_left", "color": "#FF0000", "intensity": 0.7}')
echo "$response" | grep -q '"applied":true' && echo "   ✅ Zone-specific control works" || echo "   ❌ Zone-specific control failed"
echo ""

# Test 11: Lighting effect
echo "11. Testing POST /api/lighting/effect..."
response=$(curl -s -X POST "$BASE_URL/api/lighting/effect" -H "Content-Type: application/json" -d '{"effect": "strobe", "params": {"speed": 5, "duration": 3000}}')
echo "$response" | grep -q '"started":true' && echo "   ✅ Lighting effect works" || echo "   ❌ Lighting effect failed"
echo ""

# Test 12: Transition effect
echo "12. Testing POST /api/lighting/transition..."
response=$(curl -s -X POST "$BASE_URL/api/lighting/transition" -H "Content-Type: application/json" -d '{"from": {"color": "#000000", "intensity": 0}, "to": {"color": "#FFFFFF", "intensity": 1}, "duration": 2000}')
echo "$response" | grep -q '"started":true' && echo "   ✅ Transition effect works" || echo "   ❌ Transition effect failed"
echo ""

# Test 13: Batch updates
echo "13. Testing POST /api/lighting/batch..."
response=$(curl -s -X POST "$BASE_URL/api/lighting/batch" -H "Content-Type: application/json" -d '{"updates": [{"zone": "stage_left", "color": "#FF0000", "intensity": 0.5}, {"zone": "stage_right", "color": "#00FF00", "intensity": 0.5}]}')
echo "$response" | grep -q "updated" && echo "   ✅ Batch updates works" || echo "   ❌ Batch updates failed"
echo ""

# Test 14: Reset lighting
echo "14. Testing POST /api/lighting/reset..."
response=$(curl -s -X POST "$BASE_URL/api/lighting/reset")
echo "$response" | grep -q '"reset":true' && echo "   ✅ Reset lighting works" || echo "   ❌ Reset lighting failed"
echo ""

echo "======================================"
echo "Lighting API endpoint test complete!"
echo ""
