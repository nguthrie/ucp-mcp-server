"""Tests for UCP checkout functionality.

These tests define our goals for checkout tools:
- Goal 1: Agent can create a checkout session
- Goal 2: Agent can apply discount codes
- Goal 3: Agent gets clear pricing information
"""

import pytest

from ucp_mcp_server.server import ucp_checkout_create, ucp_checkout_update


class TestCheckoutCreate:
    """Tests for the ucp_checkout_create MCP tool."""

    @pytest.mark.asyncio
    async def test_create_checkout_returns_session_id(self, mock_ucp_server):
        """Goal: Agent gets a checkout session ID to track the purchase."""
        result = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        assert "checkout_id" in result
        assert result["checkout_id"] != ""

    @pytest.mark.asyncio
    async def test_create_checkout_returns_status(self, mock_ucp_server):
        """Goal: Agent knows the checkout status."""
        result = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        assert "status" in result
        assert result["status"] == "ready_for_complete"

    @pytest.mark.asyncio
    async def test_create_checkout_returns_total(self, mock_ucp_server):
        """Goal: Agent knows the total price."""
        result = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        assert "total" in result
        assert result["total"] > 0
        assert isinstance(result["total"], int)  # Amount in cents

    @pytest.mark.asyncio
    async def test_create_checkout_returns_line_items(self, mock_ucp_server):
        """Goal: Agent can see what's in the cart."""
        result = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        assert "line_items" in result
        assert len(result["line_items"]) > 0

        item = result["line_items"][0]
        assert "id" in item
        assert "quantity" in item

    @pytest.mark.asyncio
    async def test_create_checkout_returns_currency(self, mock_ucp_server):
        """Goal: Agent knows the currency."""
        result = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
            currency="USD",
        )

        assert "currency" in result
        assert result["currency"] == "USD"


class TestCheckoutUpdate:
    """Tests for the ucp_checkout_update MCP tool."""

    @pytest.mark.asyncio
    async def test_apply_discount_code_reduces_total(self, mock_ucp_server):
        """Goal: Agent can apply promo codes and see reduced price."""
        # First create a checkout
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )
        original_total = checkout["total"]

        # Then apply discount
        result = await ucp_checkout_update(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            discount_codes=["10OFF"],
        )

        assert "total" in result
        assert result["total"] < original_total

    @pytest.mark.asyncio
    async def test_apply_discount_returns_discount_amount(self, mock_ucp_server):
        """Goal: Agent knows how much was discounted."""
        # Create checkout
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        # Apply discount
        result = await ucp_checkout_update(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            discount_codes=["10OFF"],
        )

        assert "discount_applied" in result
        assert result["discount_applied"] > 0

    @pytest.mark.asyncio
    async def test_apply_discount_returns_discount_details(self, mock_ucp_server):
        """Goal: Agent can see what discounts were applied."""
        # Create checkout
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        # Apply discount
        result = await ucp_checkout_update(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            discount_codes=["10OFF"],
        )

        assert "discounts" in result
        # The discounts dict should have info about applied codes
        assert result["discounts"] is not None

    @pytest.mark.asyncio
    async def test_update_preserves_checkout_id(self, mock_ucp_server):
        """Goal: Checkout ID remains consistent after updates."""
        # Create checkout
        checkout = await ucp_checkout_create(
            merchant_url="http://localhost:8182",
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Test User",
            buyer_email="test@example.com",
        )

        # Apply discount
        result = await ucp_checkout_update(
            merchant_url="http://localhost:8182",
            checkout_id=checkout["checkout_id"],
            discount_codes=["10OFF"],
        )

        assert result["checkout_id"] == checkout["checkout_id"]
