# Phase 3: Network Monitoring + AI Root Cause Analysis - Complete Documentation

## 🎯 Overview

Phase 3 adds powerful network monitoring, intelligent root cause analysis, and self-healing capabilities. When tests fail, the system can now:
1. Capture all network traffic and console errors
2. Automatically attempt to heal common failures
3. Generate detailed AI-powered root cause analysis
4. Stream RCA reports in real-time to the frontend

## 🏗️ Architecture

```
Playwright Engine
       ↓
   ┌───────────────────────────────┐
   │   Network Monitor (CDP)        │
   │  - Capture requests/responses  │
   │  - Console monitoring          │
   │  - Anomaly detection           │
   │  - Redis storage               │
   └───────────────┬───────────────┘
                   ↓
          Step Execution
                   ↓
              ┌─────────┐
              │ Failure?│
              └────┬────┘
                   ↓
         ┌─────────────────┐
         │   Self-Healer   │
         │ - Alt selectors │
         │ - Extended wait │
         │ - JS fallbacks  │
         │ Max 2 attempts  │
         └────┬────────────┘
              ↓
         Still failed?
              ↓
         ┌─────────────────┐
         │   RCA Engine    │
         │ - Groq LLM      │
         │ - Evidence      │
         │ - Streaming     │
         └─────────────────┘
```

## 📦 Components Built

### 1. Network Monitor (`core/network_monitor.py`)

**Purpose:** Capture network traffic and console messages using Playwright's CDP

**Features:**
✅ Automatic capture of XHR/Fetch/API calls (filters out static assets)
✅ Full request + response body capture for API calls
✅ Console message monitoring (log, warn, error)
✅ Anomaly detection:
   - HTTP status >= 400
   - Response time > 5 seconds  
   - Console errors/warnings
✅ Redis storage with 7-day TTL
✅ Per-step tracking

**Data Structure:**
```python
{
  "event_id": "uuid",
  "run_id": "run_abc123",
  "step_number": 12,
  "timestamp": "2025-01-15T10:30:00Z",
  "type": "request|response|failure|console",
  "method": "POST",
  "url": "/api/orders/create",
  "status_code": 500,
  "request_body": "...",
  "response_body": "...",
  "duration_ms": 234,
  "is_anomaly": true,
  "anomaly_reason": "HTTP 500 from order service"
}
```

**Methods:**
- `capture_request()` - Capture HTTP request
- `capture_response()` - Capture HTTP response with body
- `capture_failure()` - Capture network failure
- `capture_console()` - Capture console message
- `get_anomalies()` - Get all anomalous events
- `get_summary()` - Get statistics summary

### 2. RCA Engine (`core/llm/rca_engine.py`)

**Purpose:** AI-powered root cause analysis using Groq LLM

**LLM Configuration:**
- Model: `llama-3.3-70b-versatile`
- Temperature: `0.3` (slightly creative for analysis)
- Max tokens: `2048`
- Format: JSON object
- Streaming: Supported for real-time UX

**Input Context:**
- Failed step (description, action, error, target)
- Last 5 successful steps (context)
- Network anomalies (HTTP errors, timeouts, failures)
- Console errors and warnings
- Screenshot description
- Flow name and variables

**Output Schema:**
```json
{
  "root_cause": "The order creation API returned HTTP 500 due to missing required field 'service_location_id'",
  "affected_service": "Order Management API — /api/v1/orders",
  "failure_category": "API Error",
  "confidence": 0.87,
  "evidence": [
    "HTTP 500 at step 33 on /api/orders/create",
    "Console error: TypeError: Cannot read property 'id' of null"
  ],
  "suggested_fix": "Verify the service_location dropdown is properly loading before clicking Continue",
  "severity": "critical",
  "is_flaky": false,
  "flaky_reason": null
}
```

**Failure Categories:**
- API Error
- UI Element Missing
- Timeout
- Validation Error
- Auth Error
- Data Error
- Network Error
- JavaScript Error

**Severity Levels:**
- **critical**: Blocker, cannot proceed
- **high**: Major failure, test objective not met
- **medium**: Partial failure, some functionality works
- **low**: Minor issue, test mostly successful

**Confidence Scoring:**
- 0.9-1.0: Clear root cause with strong evidence
- 0.7-0.9: Likely cause with good evidence
- 0.5-0.7: Probable cause with some evidence
- 0.3-0.5: Possible cause with weak evidence
- 0.0-0.3: Uncertain

### 3. Self-Healer (`core/llm/self_healer.py`)

**Purpose:** Automatic healing of common test failures before marking as failed

**Healing Strategies:**

1. **Element Not Found**
   - Try alternative locator strategies in priority order
   - Ask LLM for intelligent selector suggestions (if available)
   - Confidence threshold: 0.6

2. **Timeout**
   - Wait for networkidle
   - Add 2-second buffer
   - Retry action

3. **Dropdown Selection Failed**
   - JavaScript-based selection fallback
   - Direct value assignment + change event

4. **Click Failure**
   - Force click (ignore actionability checks)
   - JavaScript click fallback

**Configuration:**
- Max attempts: `2` per step
- LLM-powered suggestions: Optional (graceful degradation)

**Logging:**
Every self-heal attempt is logged with:
- Attempt number
- Method used
- Success/failure
- Time taken

### 4. API Endpoints (`routers/network_rca.py`)

#### **GET /api/runs/{run_id}/network**
Get all captured network events

**Response:**
```json
{
  "run_id": "run_abc123",
  "summary": {
    "total_network_events": 45,
    "total_console_events": 12,
    "network_failures": 2,
    "console_errors": 3,
    "console_warnings": 1,
    "total_anomalies": 6
  },
  "network_events": [...],
  "console_events": [...],
  "anomalies": [...]
}
```

#### **POST /api/runs/{run_id}/network-events**
Receive network/console events from frontend

**Body:**
```json
[
  {
    "event_type": "response",
    "timestamp": "2025-01-15T10:30:00Z",
    "method": "POST",
    "url": "/api/orders",
    "status_code": 500,
    "duration_ms": 234
  }
]
```

#### **GET /api/runs/{run_id}/rca**
Get existing RCA report

**Response:**
```json
{
  "run_id": "run_abc123",
  "root_cause": "...",
  "affected_service": "...",
  "ai_explanation": "...",
  "suggested_fix": "...",
  "confidence_score": 0.87,
  "network_errors": {...},
  "console_errors": {...},
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### **POST /api/runs/{run_id}/rca/trigger**
Manually trigger RCA analysis

**Query Params:**
- `streaming=true` - Enable SSE streaming for real-time UX

**Streaming Response (SSE):**
```
data: {"token": "The"}
data: {"token": " order"}
data: {"token": " creation"}
...
data: [RCA_COMPLETE]{"root_cause": "...", ...}
```

**Non-streaming Response:**
```json
{
  "message": "RCA analysis complete",
  "run_id": "run_abc123",
  "rca": {...}
}
```

### 5. Integration Updates

**Playwright Engine Updates:**
- Network monitor integration
- CDP event handlers (request, response, failure)
- Console message capture
- Step number tracking
- Request/response body capture for API calls

**Celery Tasks Updates:**
- Self-healing integration
- Retry attempts logged
- Healing method tracking
- Step details with healing info

## 🧪 Testing Phase 3

### Test Network Monitoring

```bash
# Start a test run
curl -X POST http://localhost:8001/api/runs \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "create_order_single_tn",
    "variables": {...},
    "test_env_id": "env_uuid"
  }'

# Get network events
curl http://localhost:8001/api/runs/{run_id}/network

# Response will show:
# - All captured network requests/responses
# - Console errors
# - Anomalies (HTTP errors, timeouts)
```

### Test RCA (Non-Streaming)

```bash
# Trigger RCA analysis
curl -X POST "http://localhost:8001/api/runs/{run_id}/rca/trigger?streaming=false"

# Returns complete analysis:
{
  "message": "RCA analysis complete",
  "rca": {
    "root_cause": "...",
    "confidence": 0.87,
    "evidence": [...],
    "suggested_fix": "..."
  }
}

# Retrieve saved RCA
curl http://localhost:8001/api/runs/{run_id}/rca
```

### Test RCA (Streaming)

```bash
# Streaming RCA for real-time UX
curl -N "http://localhost:8001/api/runs/{run_id}/rca/trigger?streaming=true"

# Streams token-by-token:
data: {"token": "The"}
data: {"token": " order"}
data: {"token": " creation"}
data: {"token": " API"}
...
```

### Test Self-Healing

Self-healing happens automatically during test execution. Check step logs:

```bash
curl http://localhost:8001/api/runs/{run_id}/logs

# Look for steps with:
{
  "status": "success",
  "details": {
    "self_healed": true,
    "heal_method": "alternative_selector",
    "heal_attempts": 1,
    "heal_result": {...}
  }
}
```

## 📊 Real-World Examples

### Example 1: API Error Detection

**Scenario:** Order creation fails with HTTP 500

**Network Monitor Captures:**
```json
{
  "type": "response",
  "url": "/api/v1/orders",
  "status_code": 500,
  "response_body": "{\"error\": \"Missing required field: service_location_id\"}",
  "is_anomaly": true,
  "anomaly_reason": "HTTP 500 error"
}
```

**RCA Output:**
```json
{
  "root_cause": "Order Creation API returned HTTP 500 due to missing required field 'service_location_id'",
  "affected_service": "Order Management API — /api/v1/orders",
  "failure_category": "Validation Error",
  "confidence": 0.95,
  "evidence": [
    "HTTP 500 at step 33 on /api/v1/orders",
    "Response body contains: Missing required field: service_location_id",
    "Step attempted to create order without selecting service location"
  ],
  "suggested_fix": "Ensure service_location dropdown is selected before clicking Submit Order button",
  "severity": "high",
  "is_flaky": false
}
```

### Example 2: Self-Healing Success

**Scenario:** Button not found with primary selector

**Step 1: Initial Failure**
- Primary locator: `get_by_role("button", name="Submit")`
- Error: Timeout waiting for element

**Step 2: Self-Healing**
- Attempt 1: Try alternative locator
- Alternative: `get_by_text("Submit")`
- Result: ✅ Element found and clicked

**Step Log:**
```json
{
  "step_number": 14,
  "description": "Click Submit Order button",
  "status": "success",
  "details": {
    "self_healed": true,
    "heal_method": "alternative_selector",
    "heal_attempts": 1,
    "heal_result": {
      "selector_type": "text",
      "selector_value": "Submit",
      "element_found": true
    }
  }
}
```

### Example 3: Console Error Detection

**Console Monitor Captures:**
```json
{
  "type": "console",
  "console_type": "error",
  "text": "TypeError: Cannot read property 'id' of null",
  "is_anomaly": true,
  "step_number": 12
}
```

**RCA Includes:**
```json
{
  "root_cause": "JavaScript error: attempting to access 'id' property on null object",
  "failure_category": "JavaScript Error",
  "evidence": [
    "Console error: TypeError: Cannot read property 'id' of null",
    "Error occurred during step 12 (service location selection)"
  ],
  "suggested_fix": "Service location data may not be loading properly. Check API response for /api/locations endpoint"
}
```

## 🎯 Key Features

### Intelligence
✅ AI-powered root cause analysis
✅ Multi-source evidence gathering (network + console + steps)
✅ Confidence scoring and severity assessment
✅ Flaky test detection

### Self-Healing
✅ Automatic recovery from common failures
✅ 4 healing strategies
✅ Max 2 attempts per step
✅ Detailed logging of healing attempts

### Monitoring
✅ Complete network traffic capture
✅ Console error monitoring
✅ Real-time anomaly detection
✅ Per-step event tracking
✅ 7-day data retention

### User Experience
✅ Streaming RCA for real-time typing effect
✅ Frontend network event receiver
✅ Detailed network summaries
✅ Evidence-based analysis

## 🔧 Configuration

No additional configuration needed beyond Phase 2. Uses existing `GROQ_API_KEY`.

## 📚 Integration Points

### With Phase 1:
- Playwright engine enhanced with network monitor
- Step execution includes self-healing
- RCA reports stored in database

### With Phase 2:
- RCA engine uses same Groq client
- Intent parser and RCA share LLM infrastructure
- Consistent JSON output format

## 🚀 Phase 3 Status: COMPLETE ✅

All components implemented:
- ✅ Network Monitor with CDP
- ✅ RCA Engine with streaming
- ✅ Self-Healer with 4 strategies
- ✅ 4 new API endpoints
- ✅ Playwright integration
- ✅ Celery task updates

**Production-ready for advanced debugging and self-healing!** 🎉
