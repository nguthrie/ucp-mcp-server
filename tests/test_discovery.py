"""Tests for UCP discovery functionality.

These tests define our goals for the ucp_discover tool:
- Goal 1: Agent can discover what capabilities a merchant supports
- Goal 2: Agent can see available payment methods
- Goal 3: Agent gets the UCP protocol version
"""

import pytest

from ucp_mcp_server.server import ucp_discover


class TestUCPDiscover:
    """Tests for the ucp_discover MCP tool."""

    @pytest.mark.asyncio
    async def test_discover_returns_merchant_capabilities(self, mock_ucp_server):
        """Goal: Agent can discover what a merchant supports."""
        result = await ucp_discover(merchant_url="http://localhost:8182")

        # Should return capabilities
        assert "capabilities" in result
        assert len(result["capabilities"]) > 0

        # Should include checkout capability
        capability_names = [c["name"] for c in result["capabilities"]]
        assert any("checkout" in name for name in capability_names)

    @pytest.mark.asyncio
    async def test_discover_returns_payment_handlers(self, mock_ucp_server):
        """Goal: Agent knows available payment methods."""
        result = await ucp_discover(merchant_url="http://localhost:8182")

        # Should return payment handlers
        assert "payment_handlers" in result
        assert len(result["payment_handlers"]) > 0

        # Should include common handlers like google_pay
        handler_ids = [h["id"] for h in result["payment_handlers"]]
        assert "google_pay" in handler_ids or "shop_pay" in handler_ids

    @pytest.mark.asyncio
    async def test_discover_returns_ucp_version(self, mock_ucp_server):
        """Goal: Agent knows the UCP protocol version."""
        result = await ucp_discover(merchant_url="http://localhost:8182")

        assert "ucp_version" in result
        assert result["ucp_version"] != ""
        assert result["ucp_version"] != "unknown"

    @pytest.mark.asyncio
    async def test_discover_capabilities_have_required_fields(self, mock_ucp_server):
        """Goal: Each capability has name and version."""
        result = await ucp_discover(merchant_url="http://localhost:8182")

        for capability in result["capabilities"]:
            assert "name" in capability
            assert "version" in capability
            assert capability["name"] != ""

    @pytest.mark.asyncio
    async def test_discover_payment_handlers_have_required_fields(self, mock_ucp_server):
        """Goal: Each payment handler has id and name."""
        result = await ucp_discover(merchant_url="http://localhost:8182")

        for handler in result["payment_handlers"]:
            assert "id" in handler
            assert "name" in handler
            assert handler["id"] != ""
