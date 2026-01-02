"""
Unit Tests for Chat API (chat_api.py)
Tests the chat endpoint with mocked external dependencies
"""
import pytest
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.api.chat_api import (
    router,
    call_api,
    execute_tool,
    TOOLS,
    ChatRequest,
    ChatResponse
)


class TestChatAPIConstants:
    """Test TOOLS and constants"""

    def test_tools_definition_exists(self):
        """Verify TOOLS list is defined"""
        assert TOOLS is not None
        assert isinstance(TOOLS, list)
        assert len(TOOLS) > 0

    def test_tools_structure(self):
        """Verify each tool has required fields"""
        required_fields = {"name", "description", "input_schema"}

        for tool in TOOLS:
            assert all(field in tool for field in required_fields), \
                f"Tool missing required fields: {tool.get('name', 'unknown')}"

            # Verify input_schema structure
            assert "type" in tool["input_schema"]
            assert "properties" in tool["input_schema"]
            assert "required" in tool["input_schema"]

    def test_all_expected_tools_present(self):
        """Verify all expected tools are defined"""
        expected_tools = {
            "fx_get_rate",
            "fx_get_pricing_quote",
            "fx_list_deals",
            "fx_get_active_deals",
            "fx_list_cbdcs",
            "fx_list_stablecoins",
            "fx_get_segments",
            "fx_get_tiers",
            "fx_recommend_route",
            "fx_multi_rail_route",
            "fx_list_rules",
            "fx_get_rule"
        }

        actual_tools = {tool["name"] for tool in TOOLS}
        assert expected_tools == actual_tools


class TestCallAPI:
    """Test call_api function"""

    @pytest.mark.asyncio
    async def test_call_api_get_success(self):
        """Test successful GET request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rate": 83.5}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await call_api("GET", "/test", params={"pair": "USDINR"})

            assert result == {"rate": 83.5}
            mock_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_api_post_success(self):
        """Test successful POST request"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "status": "created"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await call_api("POST", "/test", json_data={"amount": 1000})

            assert result == {"id": "123", "status": "created"}
            mock_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_api_error_status(self):
        """Test API returns error status code"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await call_api("GET", "/test")

            assert "error" in result
            assert result["error"] == "API returned status 404"

    @pytest.mark.asyncio
    async def test_call_api_connection_error(self):
        """Test connection error handling"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await call_api("GET", "/test")

            assert result == {"error": "Cannot connect to API endpoint"}

    @pytest.mark.asyncio
    async def test_call_api_general_exception(self):
        """Test general exception handling"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await call_api("GET", "/test")

            assert "error" in result
            assert "Unexpected error" in result["error"]


class TestExecuteTool:
    """Test execute_tool function"""

    @pytest.mark.asyncio
    async def test_fx_get_rate(self):
        """Test fx_get_rate tool execution"""
        expected_result = {"bid": 83.45, "ask": 83.55, "mid": 83.50}

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_get_rate", {"currency_pair": "usdinr"})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with("GET", "/api/v1/fx/routing/treasury-rates/USDINR")

    @pytest.mark.asyncio
    async def test_fx_get_pricing_quote(self):
        """Test fx_get_pricing_quote tool execution"""
        expected_result = {"quote_rate": 83.60, "margin": 0.10}

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            tool_input = {
                "source_currency": "USD",
                "target_currency": "INR",
                "amount": 100000,
                "segment": "MID_MARKET",
                "direction": "SELL"
            }

            result = await execute_tool("fx_get_pricing_quote", tool_input)
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/api/v1/fx/pricing/quote"

    @pytest.mark.asyncio
    async def test_fx_list_deals_no_filter(self):
        """Test fx_list_deals without filters"""
        expected_result = [{"deal_id": "D001"}, {"deal_id": "D002"}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_list_deals", {})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with("GET", "/api/v1/fx/deals", params={})

    @pytest.mark.asyncio
    async def test_fx_list_deals_with_filters(self):
        """Test fx_list_deals with status and currency_pair filters"""
        expected_result = [{"deal_id": "D001", "status": "ACTIVE"}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            tool_input = {"status": "ACTIVE", "currency_pair": "usdinr"}
            result = await execute_tool("fx_list_deals", tool_input)
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with(
                "GET",
                "/api/v1/fx/deals",
                params={"status": "ACTIVE", "currency_pair": "USDINR"}
            )

    @pytest.mark.asyncio
    async def test_fx_get_active_deals(self):
        """Test fx_get_active_deals tool execution"""
        expected_result = [{"deal_id": "D001", "status": "ACTIVE"}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_get_active_deals", {"currency_pair": "USDINR"})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with(
                "GET",
                "/api/v1/fx/deals/active",
                params={"currency_pair": "USDINR"}
            )

    @pytest.mark.asyncio
    async def test_fx_list_cbdcs(self):
        """Test fx_list_cbdcs tool execution"""
        expected_result = [{"code": "e-INR", "name": "Digital Rupee"}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_list_cbdcs", {})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with("GET", "/api/v1/fx/multi-rail/cbdc")

    @pytest.mark.asyncio
    async def test_fx_list_stablecoins(self):
        """Test fx_list_stablecoins tool execution"""
        expected_result = [{"code": "USDC", "name": "USD Coin"}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_list_stablecoins", {})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with("GET", "/api/v1/fx/multi-rail/stablecoins")

    @pytest.mark.asyncio
    async def test_fx_get_segments(self):
        """Test fx_get_segments tool execution"""
        expected_result = [{"segment": "RETAIL", "margin": 0.5}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_get_segments", {})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with("GET", "/api/v1/fx/pricing/segments")

    @pytest.mark.asyncio
    async def test_fx_get_tiers(self):
        """Test fx_get_tiers tool execution"""
        expected_result = [{"tier": "PLATINUM", "discount": 0.05}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_get_tiers", {})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with("GET", "/api/v1/fx/pricing/tiers")

    @pytest.mark.asyncio
    async def test_fx_recommend_route(self):
        """Test fx_recommend_route tool execution"""
        expected_result = {"provider": "Provider1", "rate": 83.55}

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            tool_input = {
                "currency_pair": "USDINR",
                "amount": 100000,
                "side": "SELL",
                "customer_tier": "GOLD"
            }

            result = await execute_tool("fx_recommend_route", tool_input)
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_fx_multi_rail_route(self):
        """Test fx_multi_rail_route tool execution"""
        expected_result = {"route": "SWIFT", "cost": 25.50}

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            tool_input = {
                "source_currency": "USD",
                "target_currency": "INR",
                "amount": 100000
            }

            result = await execute_tool("fx_multi_rail_route", tool_input)
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_fx_list_rules_no_filter(self):
        """Test fx_list_rules without filters"""
        expected_result = [{"rule_id": "PROV-001", "type": "PROVIDER_SELECTION"}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_list_rules", {})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with("GET", "/api/v1/fx/rules/", params={})

    @pytest.mark.asyncio
    async def test_fx_list_rules_with_filters(self):
        """Test fx_list_rules with rule_type and enabled filters"""
        expected_result = [{"rule_id": "MARGIN-001", "enabled": True}]

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            tool_input = {"rule_type": "margin_adjustment", "enabled": True}
            result = await execute_tool("fx_list_rules", tool_input)
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with(
                "GET",
                "/api/v1/fx/rules/",
                params={"rule_type": "MARGIN_ADJUSTMENT", "enabled": True}
            )

    @pytest.mark.asyncio
    async def test_fx_get_rule(self):
        """Test fx_get_rule tool execution"""
        expected_result = {"rule_id": "PROV-001", "type": "PROVIDER_SELECTION"}

        with patch('app.api.chat_api.call_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_result

            result = await execute_tool("fx_get_rule", {"rule_id": "PROV-001"})
            result_data = json.loads(result)

            assert result_data == expected_result
            mock_call.assert_called_once_with("GET", "/api/v1/fx/rules/PROV-001")

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Test handling of unknown tool name"""
        result = await execute_tool("unknown_tool", {})
        result_data = json.loads(result)

        assert "error" in result_data
        assert "Unknown tool" in result_data["error"]


class TestChatModels:
    """Test Pydantic models"""

    def test_chat_request_model(self):
        """Test ChatRequest model"""
        request = ChatRequest(message="What is the rate for USDINR?")
        assert request.message == "What is the rate for USDINR?"

    def test_chat_response_model(self):
        """Test ChatResponse model"""
        response = ChatResponse(response="The current rate is 83.50")
        assert response.response == "The current rate is 83.50"


class TestChatEndpoint:
    """Test the /chat endpoint"""

    def setup_method(self):
        """Setup test client"""
        from app.main import app
        self.client = TestClient(app)

    @patch('app.api.chat_api.get_settings')
    def test_chat_no_api_key(self, mock_settings):
        """Test chat endpoint without ANTHROPIC_API_KEY"""
        mock_settings.return_value.anthropic_api_key = None

        response = self.client.post(
            "/api/v1/fx/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "ANTHROPIC_API_KEY" in data["response"]

    @patch('app.api.chat_api.get_settings')
    @patch('httpx.AsyncClient')
    def test_chat_api_error(self, mock_httpx, mock_settings):
        """Test chat endpoint with API error"""
        mock_settings.return_value.anthropic_api_key = "test-key"

        # Mock the httpx client
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        response = self.client.post(
            "/api/v1/fx/chat",
            json={"message": "What is the rate?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "API error" in data["response"]

    @patch('app.api.chat_api.get_settings')
    @patch('httpx.AsyncClient')
    def test_chat_timeout(self, mock_httpx, mock_settings):
        """Test chat endpoint with timeout"""
        mock_settings.return_value.anthropic_api_key = "test-key"

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        response = self.client.post(
            "/api/v1/fx/chat",
            json={"message": "What is the rate?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "timed out" in data["response"]

    @patch('app.api.chat_api.get_settings')
    @patch('httpx.AsyncClient')
    def test_chat_successful_response_no_tools(self, mock_httpx, mock_settings):
        """Test successful chat response without tool use"""
        mock_settings.return_value.anthropic_api_key = "test-key"

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Hello! How can I help you?"}],
            "stop_reason": "end_turn"
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        response = self.client.post(
            "/api/v1/fx/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! How can I help you?"

    @patch('app.api.chat_api.get_settings')
    @patch('httpx.AsyncClient')
    @patch('app.api.chat_api.execute_tool')
    def test_chat_with_tool_use(self, mock_execute_tool, mock_httpx, mock_settings):
        """Test chat with tool use"""
        mock_settings.return_value.anthropic_api_key = "test-key"
        mock_execute_tool.return_value = json.dumps({"bid": 83.45, "ask": 83.55})

        # First response with tool use
        tool_use_response = Mock()
        tool_use_response.status_code = 200
        tool_use_response.json.return_value = {
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_1",
                    "name": "fx_get_rate",
                    "input": {"currency_pair": "USDINR"}
                }
            ],
            "stop_reason": "tool_use"
        }

        # Second response after tool result
        final_response = Mock()
        final_response.status_code = 200
        final_response.json.return_value = {
            "content": [{"type": "text", "text": "The current rate is 83.50"}],
            "stop_reason": "end_turn"
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(side_effect=[tool_use_response, final_response])
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        response = self.client.post(
            "/api/v1/fx/chat",
            json={"message": "What is the USDINR rate?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "rate" in data["response"].lower()
        mock_execute_tool.assert_called_once()

    @patch('app.api.chat_api.get_settings')
    @patch('httpx.AsyncClient')
    def test_chat_general_exception(self, mock_httpx, mock_settings):
        """Test chat endpoint with general exception"""
        mock_settings.return_value.anthropic_api_key = "test-key"

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(side_effect=Exception("Unexpected error"))
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        response = self.client.post(
            "/api/v1/fx/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "Error:" in data["response"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
