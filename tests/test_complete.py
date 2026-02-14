"""Tests for UCP checkout completion (payment) functionality.

These tests define our goals for the checkout complete tool:
- Goal 1: Agent can complete a checkout and get an order ID
- Goal 2: Agent gets confirmation that the status is 'complete'
- Goal 3: Agent gets an order permalink for tracking
"""

import pytest

from ucp_mcp_server.server import ucp_checkout_complete, ucp_checkout_create


class TestCheckoutComplete:
    """Tests for the ucp_checkout_complete MCP tool."""

    @pytest.mark.asyncio
    async def test_complete_returns_order_id(self, mock_ucp_server):
        """Goal: Agent gets an order ID after payment."""
        # Create checkout first
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        result = await ucp_checkout_complete(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            payment_handler_id="mock_payment_handler",
        )

        assert "order_id" in result
        assert result["order_id"] != ""

    @pytest.mark.asyncio
    async def test_complete_returns_status_complete(self, mock_ucp_server):
        """Goal: Status changes to 'complete' after payment."""
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        result = await ucp_checkout_complete(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            payment_handler_id="mock_payment_handler",
        )

        assert result["status"] == "complete"

    @pytest.mark.asyncio
    async def test_complete_returns_order_url(self, mock_ucp_server):
        """Goal: Agent gets a permalink to track the order."""
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        result = await ucp_checkout_complete(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            payment_handler_id="mock_payment_handler",
        )

        assert "order_url" in result
        assert result["order_url"] is not None

    @pytest.mark.asyncio
    async def test_complete_returns_final_total(self, mock_ucp_server):
        """Goal: Agent knows the final amount charged."""
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        result = await ucp_checkout_complete(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            payment_handler_id="mock_payment_handler",
        )

        assert "total" in result
        assert result["total"] > 0

    @pytest.mark.asyncio
    async def test_complete_preserves_checkout_id(self, mock_ucp_server):
        """Goal: Checkout ID is consistent."""
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        result = await ucp_checkout_complete(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            payment_handler_id="mock_payment_handler",
        )

        assert result["checkout_id"] == checkout["checkout_id"]


class TestCheckoutCompleteErrors:
    """Tests for error handling during checkout completion."""

    @pytest.mark.asyncio
    async def test_complete_invalid_checkout_returns_error(self):
        """Goal: Invalid checkout ID returns clear error."""
        import respx
        from httpx import Response

        with respx.mock(assert_all_called=False) as mock:
            mock.post(
                "http://localhost:8182/checkout-sessions/invalid-id/complete"
            ).mock(return_value=Response(404, json={"error": "Checkout not found"}))

            result = await ucp_checkout_complete(
                merchant_url="http://localhost:8182",
                checkout_id="invalid-id",
                payment_handler_id="mock_payment_handler",
            )

            assert "error" in result

    @pytest.mark.asyncio
    async def test_complete_payment_failure_returns_error(self):
        """Goal: Payment failures return clear error."""
        import respx
        from httpx import Response

        with respx.mock(assert_all_called=False) as mock:
            mock.post(
                url__regex=r"http://localhost:8182/checkout-sessions/.*/complete"
            ).mock(return_value=Response(400, json={"error": "Payment declined"}))

            result = await ucp_checkout_complete(
                merchant_url="http://localhost:8182",
                checkout_id="some-checkout-id",
                payment_handler_id="mock_payment_handler",
                card_token="fail_token",
            )

            assert "error" in result
