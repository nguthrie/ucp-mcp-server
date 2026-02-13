"""Tests for error handling.

These tests define our goals for error handling:
- Goal 1: Clear errors when merchant is unreachable
- Goal 2: Errors include helpful context
- Goal 3: Errors don't crash the server (return error dict instead)
"""

import pytest
import respx
from httpx import Response

from ucp_mcp_server.server import ucp_discover, ucp_checkout_create, ucp_checkout_update


class TestConnectionErrors:
    """Tests for handling connection failures."""

    @pytest.mark.asyncio
    async def test_invalid_merchant_returns_error_dict(self, mock_invalid_server):
        """Goal: Returns error dict instead of raising exception."""
        result = await ucp_discover(merchant_url="http://invalid.example")

        assert "error" in result
        assert isinstance(result["error"], str)

    @pytest.mark.asyncio
    async def test_invalid_merchant_error_is_descriptive(self, mock_invalid_server):
        """Goal: Error message helps user understand the problem."""
        result = await ucp_discover(merchant_url="http://invalid.example")

        assert "error" in result
        # Should mention connection issue
        error_lower = result["error"].lower()
        assert "connect" in error_lower or "merchant" in error_lower

    @pytest.mark.asyncio
    async def test_checkout_with_invalid_merchant_returns_error(self, mock_invalid_server):
        """Goal: Checkout also handles connection errors gracefully."""
        # Set up mock for checkout endpoint
        with respx.mock(assert_all_called=False) as mock:
            import httpx
            mock.post("http://invalid.example/checkout-sessions").mock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            result = await ucp_checkout_create(
                merchant_url="http://invalid.example",
                items=[{"id": "test", "quantity": 1}],
                buyer_name="Test",
                buyer_email="test@example.com",
            )

            assert "error" in result


class TestHTTPErrors:
    """Tests for handling HTTP errors from merchants."""

    @pytest.mark.asyncio
    async def test_404_returns_error(self):
        """Goal: HTTP 404 errors are handled gracefully."""
        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://localhost:8182/.well-known/ucp").mock(
                return_value=Response(404, text="Not Found")
            )

            result = await ucp_discover(merchant_url="http://localhost:8182")

            assert "error" in result

    @pytest.mark.asyncio
    async def test_500_returns_error(self):
        """Goal: HTTP 500 errors are handled gracefully."""
        with respx.mock(assert_all_called=False) as mock:
            mock.get("http://localhost:8182/.well-known/ucp").mock(
                return_value=Response(500, text="Internal Server Error")
            )

            result = await ucp_discover(merchant_url="http://localhost:8182")

            assert "error" in result
            assert "error" in result["error"].lower() or "500" in result["error"]

    @pytest.mark.asyncio
    async def test_checkout_400_returns_error(self):
        """Goal: Bad request errors return helpful info."""
        with respx.mock(assert_all_called=False) as mock:
            mock.post("http://localhost:8182/checkout-sessions").mock(
                return_value=Response(400, json={"error": "Invalid product ID"})
            )

            result = await ucp_checkout_create(
                merchant_url="http://localhost:8182",
                items=[{"id": "nonexistent", "quantity": 1}],
                buyer_name="Test",
                buyer_email="test@example.com",
            )

            assert "error" in result


class TestUpdateErrors:
    """Tests for handling update errors."""

    @pytest.mark.asyncio
    async def test_update_nonexistent_checkout_returns_error(self):
        """Goal: Invalid checkout ID returns clear error."""
        with respx.mock(assert_all_called=False) as mock:
            mock.put("http://localhost:8182/checkout-sessions/invalid-id").mock(
                return_value=Response(404, json={"error": "Checkout not found"})
            )

            result = await ucp_checkout_update(
                merchant_url="http://localhost:8182",
                checkout_id="invalid-id",
                discount_codes=["10OFF"],
            )

            assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_discount_code_returns_error(self):
        """Goal: Invalid discount codes return clear error."""
        with respx.mock(assert_all_called=False) as mock:
            mock.put(url__regex=r"http://localhost:8182/checkout-sessions/.*").mock(
                return_value=Response(400, json={"error": "Invalid discount code"})
            )

            result = await ucp_checkout_update(
                merchant_url="http://localhost:8182",
                checkout_id="some-checkout-id",
                discount_codes=["INVALID_CODE"],
            )

            assert "error" in result
