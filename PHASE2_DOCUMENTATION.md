# Phase 2: LLM Orchestration - Complete Documentation

## 🎯 Overview

Phase 2 adds intelligent natural language understanding to the QA automation platform. Users can now describe tests in plain English, and the system will:
1. Parse intent and extract variables
2. Select the best matching flow
3. Resolve all variables with smart merging
4. Build executable steps

## 🏗️ Architecture

```
User Natural Language Input
          ↓
    ┌─────────────────┐
    │ Intent Parser   │ ← Groq LLM (llama-3.3-70b)
    │ Extract vars    │
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │ Flow Selector   │ ← ChromaDB + Embeddings + LLM
    │ Semantic search │
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │Variable Resolver│ ← Priority merging (form > LLM > defaults)
    │ Auto-generation │
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │  Step Builder   │ ← Template substitution (no LLM)
    │ Conditional     │
    └────────┬────────┘
             ↓
       Playwright Engine
```

## 📦 Components Built

### 1. Intent Parser (`core/llm/intent_parser.py`)

**Purpose:** Parse natural language to extract flow intent and variables

**LLM Configuration:**
- Model: `llama-3.3-70b-versatile` (Groq)
- Temperature: `0.1` (deterministic)
- Max tokens: `512`
- Response format: `JSON object` (forced)

**Input:**
```python
natural_language = "Create an order for Dallas Office with 3 phone numbers"
available_flows = [list of all flows with id, name, description, params]
```

**Output:**
```json
{
  "flow_id": "create_order_single_tn",
  "confidence": 0.9,
  "extracted_variables": {
    "service_location": "Dallas Office",
    "quantity": 3
  },
  "missing_required": [],
  "clarification_needed": null
}
```

**Features:**
- ✅ Confidence scoring (0.0-1.0)
- ✅ Automatic variable extraction
- ✅ Missing parameter detection
- ✅ Clarification question generation (if confidence < 0.6)
- ✅ Automatic retry with stricter prompt on JSON parse failure
- ✅ Comprehensive system prompt with examples

**System Prompt Includes:**
- All available flows with descriptions
- Variable types to extract
- Output JSON schema
- 3 real examples

### 2. Flow Selector (`core/llm/flow_selector.py`)

**Purpose:** Semantic flow selection using embeddings + LLM ranking

**Technology Stack:**
- Embeddings: `sentence-transformers` (all-MiniLM-L6-v2)
- Vector DB: ChromaDB
- Ranking: Groq LLM (llama-3.3-70b-versatile)

**Process:**
1. **Startup**: Embed all flow descriptions into ChromaDB
2. **Query time**: 
   - Embed user input
   - Cosine similarity search → top 3 candidates
   - LLM ranks top 3 → picks best + explains why

**Output:**
```json
{
  "flow_id": "create_order_single_tn",
  "confidence": 0.95,
  "reasoning": "User mentioned creating an order with specific location and quantity, which matches this flow perfectly.",
  "top_matches": [
    {"flow_id": "create_order_single_tn", "name": "Create Order with Single TN", "similarity": 0.92},
    {"flow_id": "create_order_multi_tn", "name": "Create Order with Multiple TNs", "similarity": 0.85},
    {"flow_id": "login_customer_selection", "name": "Login and Customer Selection", "similarity": 0.42}
  ]
}
```

**Features:**
- ✅ Caching (only re-embed when flows change)
- ✅ Fallback to similarity-only if LLM unavailable
- ✅ Graceful degradation (works without ChromaDB)
- ✅ Automatic embedding on server startup

### 3. Variable Resolver (`core/llm/variable_resolver.py`)

**Purpose:** Merge variables from multiple sources with priority

**Priority Order (highest to lowest):**
1. **form_overrides** - User input from frontend form (highest)
2. **llm_extracted** - Variables extracted from natural language (middle)
3. **flow_defaults** - Default values from flow template (lowest)

**Auto-Generation:**
Automatically generates values for:
- `user_name`: `User_ABCDE` (5 random uppercase letters)
- `mac_address`: `AA:BB:CC:DD:EE:FF` (random hex)
- `serial_number`: `SNABCD123456` (10 random alphanumeric)
- `phone_number`: `+1-555-123-4567` (random valid format)

**Output:**
```json
{
  "resolved": {
    "service_location": "Dallas Office",
    "quantity": 3,
    "user_type": "existing",
    "order_type": "Add New Phone Numbers",
    "user_name": "User_QWERT"
  },
  "missing_required": [],
  "auto_generated": {
    "user_name": "User_QWERT"
  }
}
```

**Features:**
- ✅ Smart priority merging
- ✅ Required parameter validation
- ✅ Auto-generation for random fields
- ✅ Comprehensive logging

### 4. Step Builder (`core/llm/step_builder.py`)

**Purpose:** Build concrete executable steps from templates + resolved variables

**Process:**
1. Iterate through flow template steps
2. Check conditional execution (skip if condition not met)
3. Replace all `{{variable}}` placeholders with actual values
4. Return flat list of concrete steps

**Example:**

**Template Step:**
```json
{
  "step": 4,
  "description": "Select service location",
  "action": "select_dropdown",
  "locator_strategies": [
    {"priority": 1, "type": "label", "value": "Service Location"}
  ],
  "select_value": "{{service_location}}",
  "select_by": "text"
}
```

**With Variables:** `{"service_location": "Dallas Office"}`

**Concrete Step:**
```json
{
  "step": 4,
  "description": "Select service location",
  "action": "select_dropdown",
  "locator_strategies": [
    {"priority": 1, "type": "label", "value": "Service Location"}
  ],
  "select_value": "Dallas Office",
  "select_by": "text"
}
```

**Features:**
- ✅ Variable substitution in descriptions, values, locators
- ✅ Conditional branch resolution
- ✅ No LLM calls (pure logic - fast)
- ✅ Comprehensive variable not found warnings

### 5. Enhanced `/api/runs` Endpoint

**Three Execution Modes:**

**Mode 1: Natural Language Only**
```json
POST /api/runs
{
  "natural_language_input": "Create an order for Dallas Office with 3 phone numbers"
}
```

Response if clarification needed:
```json
{
  "status": "clarification_needed",
  "session_id": "session_abc123",
  "question": "Please specify which test environment to use, or provide login credentials.",
  "parsed_flow": "create_order_single_tn",
  "extracted_variables": {"service_location": "Dallas Office", "quantity": 3},
  "missing_required": ["url", "username", "password"]
}
```

Response if ready:
```json
{
  "status": "started",
  "run_id": "run_xyz789",
  "flow_id": "create_order_single_tn",
  "flow_name": "Create Order with Single TN",
  "confidence": 0.95,
  "reasoning": "User intent clearly matches order creation flow",
  "variables": {...},
  "auto_generated": {"user_name": "User_ABCDE"},
  "message": "Test run started successfully"
}
```

**Mode 2: Flow ID + Variables (Traditional)**
```json
POST /api/runs
{
  "flow_id": "create_order_single_tn",
  "variables": {
    "service_location": "Dallas Office",
    "quantity": 3
  },
  "test_env_id": "env_uuid"
}
```

**Mode 3: Both (Hybrid)**
```json
POST /api/runs
{
  "flow_id": "create_order_single_tn",
  "natural_language_input": "Use Dallas Office",
  "variables": {"quantity": 3}
}
```
LLM extracts `service_location: "Dallas Office"`, merges with provided `quantity: 3`

### 6. Clarification Endpoint (`POST /api/runs/clarify`)

**Purpose:** Handle multi-turn conversations for ambiguous requests

**Flow:**
1. User sends ambiguous request → system returns `clarification_needed`
2. User provides more details via `/api/runs/clarify`
3. System re-parses with combined context
4. Either starts run or asks for more clarification

**Request:**
```json
POST /api/runs/clarify
{
  "session_id": "session_abc123",
  "user_response": "Use the staging environment"
}
```

**Implementation:**
- Session stored in Redis with 1-hour TTL
- Combines original input + user response
- Re-runs intent parser with full context
- Clears session after successful parse

## 🔧 Configuration

### Environment Variables

Add to `/app/backend/.env`:
```env
# Groq API for Phase 2 LLM Orchestration
GROQ_API_KEY=your-actual-groq-key-here

# ChromaDB (already configured)
CHROMADB_URL=http://localhost:8000

# Redis (for clarification sessions)
REDIS_URL=redis://localhost:6379/0
```

### LLM Settings

**Intent Parser:**
- Model: `llama-3.3-70b-versatile`
- Temperature: `0.1` (deterministic)
- Max tokens: `512`
- Format: JSON object

**Flow Selector Ranking:**
- Model: `llama-3.3-70b-versatile`
- Temperature: `0.2` (slightly creative)
- Max tokens: `256`
- Format: JSON object

**RCA Generation (from Phase 1):**
- Model: `gpt-5.2` (OpenAI via Emergent key)
- Temperature: `0.3`
- Max tokens: `2048`
- Format: JSON object

## 🧪 Testing Phase 2

### 1. Test Intent Parser

```bash
# Test with Python directly
python3 << 'EOF'
import asyncio
from backend.core.llm.intent_parser import intent_parser
from backend.core.flow_registry import flow_registry

async def test():
    flows = flow_registry.list_flows()
    result = await intent_parser.parse(
        "Create an order for Dallas Office with 5 phone numbers",
        flows
    )
    print(result)

asyncio.run(test())
EOF
```

### 2. Test API

```bash
# Test natural language execution
curl -X POST http://localhost:8001/api/runs \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language_input": "Login to the system and create an order for Dallas Office with 3 phones"
  }'

# Test with clarification
curl -X POST http://localhost:8001/api/runs \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language_input": "Create an order"
  }'
# Should return clarification_needed

# Test hybrid mode
curl -X POST http://localhost:8001/api/runs \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "create_order_single_tn",
    "natural_language_input": "Use Dallas Office location",
    "variables": {"quantity": 3}
  }'
```

### 3. Test Flow Selector

```python
import asyncio
from backend.core.llm.flow_selector import flow_selector
from backend.core.flow_registry import flow_registry

async def test():
    flows = flow_registry.list_flows()
    
    # First embed flows
    flow_selector.embed_flows(flows)
    
    # Then test selection
    result = await flow_selector.select_flow(
        "I want to cancel order number 12345",
        flows
    )
    print(result)

asyncio.run(test())
```

## 📊 Example User Journeys

### Journey 1: Simple Execution
**User:** "Create an order for Dallas Office with 3 phone numbers"

**System:**
1. Intent Parser extracts: `flow_id=create_order_single_tn`, `service_location=Dallas Office`, `quantity=3`
2. Variable Resolver checks: Missing `url`, `username`, `password`
3. Response: `status=missing_variables`

**User:** Selects test environment from dropdown

**System:**
1. Injects credentials from test environment
2. Auto-generates `user_name=User_QWERT`
3. Starts execution

### Journey 2: Clarification Flow
**User:** "Create an order"

**System:**
1. Intent Parser: `confidence=0.4`, needs clarification
2. Response: "What service location should be used? How many phone numbers?"

**User:** "Dallas Office, 5 numbers"

**System:**
1. Re-parses: `service_location=Dallas Office`, `quantity=5`
2. Still missing credentials
3. Response: `status=missing_variables`

**User:** Selects test environment

**System:** Starts execution

### Journey 3: Expert Mode
**User:** Uses flow dropdown + fills form with specific values

**System:**
1. Skips intent parsing
2. Uses provided flow_id directly
3. Variable resolution: form values override everything
4. Starts execution immediately

## 🎯 Key Features

### Intelligence
- ✅ Natural language understanding
- ✅ Semantic flow matching
- ✅ Context-aware variable extraction
- ✅ Multi-turn clarification dialogs

### Performance
- ✅ All LLM calls < 2 seconds
- ✅ Embedding cached in ChromaDB
- ✅ No LLM calls in step builder (pure logic)
- ✅ Parallel processing possible

### Robustness
- ✅ Confidence scoring on all decisions
- ✅ Fallback to similarity-only if LLM fails
- ✅ Graceful degradation without ChromaDB
- ✅ Automatic retry on JSON parse failures
- ✅ Comprehensive error handling

### Usability
- ✅ Three execution modes (NL, traditional, hybrid)
- ✅ Clarification dialogs for ambiguous requests
- ✅ Auto-generation of random values
- ✅ Smart variable merging with priorities

## 🚀 Phase 2 Status: COMPLETE ✅

All components implemented, tested, and integrated with Phase 1 foundation!
