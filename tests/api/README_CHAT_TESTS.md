# Chat API Unit Tests

This document describes the unit tests for `app/api/chat_api.py`.

## Test File

- **Location**: `tests/api/test_chat_api.py`
- **Framework**: pytest with pytest-asyncio
- **Type**: Unit tests with mocked dependencies

## Test Coverage

The test suite covers the following components:

### 1. Constants and Configuration (`TestChatAPIConstants`)
- ✓ Verifies TOOLS list is defined
- ✓ Validates tool structure (name, description, input_schema)
- ✓ Ensures all expected tools are present

### 2. API Call Function (`TestCallAPI`)
- ✓ Successful GET requests
- ✓ Successful POST requests
- ✓ Error status code handling (404, 500, etc.)
- ✓ Connection error handling
- ✓ General exception handling

### 3. Tool Execution (`TestExecuteTool`)
Tests all 12 FX tools:
- ✓ `fx_get_rate` - Get FX rates
- ✓ `fx_get_pricing_quote` - Get pricing quotes
- ✓ `fx_list_deals` - List deals (with/without filters)
- ✓ `fx_get_active_deals` - Get active deals
- ✓ `fx_list_cbdcs` - List CBDCs
- ✓ `fx_list_stablecoins` - List stablecoins
- ✓ `fx_get_segments` - Get customer segments
- ✓ `fx_get_tiers` - Get pricing tiers
- ✓ `fx_recommend_route` - Get route recommendations
- ✓ `fx_multi_rail_route` - Get multi-rail routing
- ✓ `fx_list_rules` - List FX rules
- ✓ `fx_get_rule` - Get specific rule
- ✓ Unknown tool handling

### 4. Pydantic Models (`TestChatModels`)
- ✓ ChatRequest model validation
- ✓ ChatResponse model validation

### 5. Chat Endpoint (`TestChatEndpoint`)
- ✓ Missing API key handling
- ✓ API error responses
- ✓ Timeout handling
- ✓ Successful responses without tools
- ✓ Successful responses with tool use
- ✓ General exception handling

## Prerequisites

Install required dependencies:

```bash
pip install pytest pytest-asyncio httpx fastapi python-dotenv
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## Running the Tests

### Run all chat API tests:
```bash
pytest tests/api/test_chat_api.py -v
```

### Run specific test class:
```bash
# Test only the execute_tool function
pytest tests/api/test_chat_api.py::TestExecuteTool -v

# Test only the chat endpoint
pytest tests/api/test_chat_api.py::TestChatEndpoint -v
```

### Run specific test:
```bash
pytest tests/api/test_chat_api.py::TestExecuteTool::test_fx_get_rate -v
```

### Run with coverage:
```bash
pytest tests/api/test_chat_api.py --cov=app.api.chat_api --cov-report=html
```

### Run with detailed output:
```bash
pytest tests/api/test_chat_api.py -vv -s
```

## Test Statistics

- **Total Test Classes**: 5
- **Total Test Methods**: 35+
- **Coverage Areas**:
  - Configuration & Constants
  - HTTP Client Operations
  - All Tool Executions
  - Model Validation
  - Endpoint Integration

## Mock Strategy

The tests use Python's `unittest.mock` to mock:

1. **External API calls** (`httpx.AsyncClient`)
2. **Anthropic API** (Claude API responses)
3. **Internal API calls** (`call_api` function)
4. **Settings/Configuration** (`get_settings`)

This ensures tests run:
- ✓ Fast (no network calls)
- ✓ Reliably (no external dependencies)
- ✓ Safely (no API costs)

## Example Test Output

```
tests/api/test_chat_api.py::TestChatAPIConstants::test_tools_definition_exists PASSED
tests/api/test_chat_api.py::TestChatAPIConstants::test_tools_structure PASSED
tests/api/test_chat_api.py::TestCallAPI::test_call_api_get_success PASSED
tests/api/test_chat_api.py::TestExecuteTool::test_fx_get_rate PASSED
tests/api/test_chat_api.py::TestChatEndpoint::test_chat_successful_response_no_tools PASSED
...
================================ 35 passed in 0.45s =================================
```

## Troubleshooting

### Import Errors
If you see import errors, ensure you're running from the project root:
```bash
cd /path/to/FX-MS
pytest tests/api/test_chat_api.py -v
```

### Module Not Found
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Async Test Warnings
Install pytest-asyncio:
```bash
pip install pytest-asyncio
```

## Notes

- Tests are independent and can run in any order
- All external dependencies are mocked
- Tests verify both success and error paths
- Coverage includes edge cases and exceptions
