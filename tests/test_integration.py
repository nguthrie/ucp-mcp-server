"""Integration tests against real UCP servers.

These tests are designed to run against the UCP sample flower shop server.
They are marked with @pytest.mark.integration and skipped by default.

To run these tests:
1. Start the UCP sample flower shop server on port 8182
2. Run: pytest tests/test_integration.py -v -m integration --run-integration

Setup instructions for the flower shop server:
```bash
# Clone and set up the UCP samples
git clone https://github.com/Universal-Commerce-Protocol/python-sdk.git sdk/python
git clone https://github.com/Universal-Commerce-Protocol/samples.git
cd samples/rest/python/server
uv sync

# Create database with sample products
mkdir /tmp/ucp_test
uv run import_csv.py \
    --products_db_path=/tmp/ucp_test/products.db \
    --transactions_db_path=/tmp/ucp_test/transactions.db \
    --data_dir=../test_data/flower_shop

# Start the server
uv run server.py \
    --products_db_path=/tmp/ucp_test/products.db \
    --transactions_db_path=/tmp/ucp_test/transactions.db \
    --port=8182
```
"""

import os

import pytest

from ucp_mcp_server.server import ucp_discover, ucp_checkout_create, ucp_checkout_update


# Skip integration tests by default
pytestmark = pytest.mark.integration


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires live server)"
    )


@pytest.fixture
def integration_server_url():
    """Get the integration server URL from environment or default."""
    return os.environ.get("UCP_TEST_SERVER", "http://localhost:8182")


@pytest.fixture
def skip_if_no_server(integration_server_url):
    """Skip test if integration server is not available."""
    import httpx

    try:
        response = httpx.get(f"{integration_server_url}/.well-known/ucp", timeout=5.0)
        if response.status_code != 200:
            pytest.skip(f"Integration server not responding correctly at {integration_server_url}")
    except Exception as e:
        pytest.skip(f"Integration server not available at {integration_server_url}: {e}")


class TestIntegrationDiscovery:
    """Integration tests for discovery against real server."""

    @pytest.mark.asyncio
    async def test_discover_real_flower_shop(self, integration_server_url, skip_if_no_server):
        """Test discovery against real flower shop server."""
        result = await ucp_discover(merchant_url=integration_server_url)

        # Should have no error
        assert "error" not in result, f"Got error: {result.get('error')}"

        # Should have capabilities
        assert "capabilities" in result
        assert len(result["capabilities"]) > 0

        # Should include checkout capability
        capability_names = [c["name"] for c in result["capabilities"]]
        assert any("checkout" in name for name in capability_names)

        # Should have payment handlers
        assert "payment_handlers" in result

        print(f"\nDiscovered capabilities: {capability_names}")
        print(f"Payment handlers: {[h['id'] for h in result['payment_handlers']]}")


class TestIntegrationCheckout:
    """Integration tests for checkout against real server."""

    @pytest.mark.asyncio
    async def test_create_checkout_with_real_product(
        self, integration_server_url, skip_if_no_server
    ):
        """Test creating checkout with a real product."""
        result = await ucp_checkout_create(
            merchant_url=integration_server_url,
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Integration Test",
            buyer_email="integration@test.com",
        )

        # Should have no error
        assert "error" not in result, f"Got error: {result.get('error')}"

        # Should have checkout ID
        assert "checkout_id" in result
        assert result["checkout_id"] != ""

        # Should have status
        assert result["status"] == "ready_for_complete"

        # Should have total > 0
        assert result["total"] > 0

        print(f"\nCreated checkout: {result['checkout_id']}")
        print(f"Total: ${result['total'] / 100:.2f}")

    @pytest.mark.asyncio
    async def test_apply_discount_to_real_checkout(
        self, integration_server_url, skip_if_no_server
    ):
        """Test applying discount to real checkout."""
        # Create checkout first
        checkout = await ucp_checkout_create(
            merchant_url=integration_server_url,
            items=[{"id": "bouquet_roses", "quantity": 1}],
            buyer_name="Integration Test",
            buyer_email="integration@test.com",
        )

        assert "error" not in checkout, f"Checkout error: {checkout.get('error')}"
        original_total = checkout["total"]

        # Apply discount
        result = await ucp_checkout_update(
            merchant_url=integration_server_url,
            checkout_id=checkout["checkout_id"],
            discount_codes=["10OFF"],
        )

        # Should have no error
        assert "error" not in result, f"Got error: {result.get('error')}"

        # Total should be reduced
        assert result["total"] < original_total

        print(f"\nOriginal total: ${original_total / 100:.2f}")
        print(f"Discounted total: ${result['total'] / 100:.2f}")
        print(f"Saved: ${(original_total - result['total']) / 100:.2f}")


class TestIntegrationFullFlow:
    """Integration test for complete shopping flow."""

    @pytest.mark.asyncio
    async def test_complete_shopping_flow(self, integration_server_url, skip_if_no_server):
        """Test complete flow: discover -> checkout -> discount."""
        # Step 1: Discover capabilities
        discovery = await ucp_discover(merchant_url=integration_server_url)
        assert "error" not in discovery
        print("\n--- Step 1: Discovery ---")
        print(f"Found {len(discovery['capabilities'])} capabilities")
        print(f"Found {len(discovery['payment_handlers'])} payment handlers")

        # Step 2: Create checkout
        checkout = await ucp_checkout_create(
            merchant_url=integration_server_url,
            items=[
                {"id": "bouquet_roses", "quantity": 2},
            ],
            buyer_name="Full Flow Test",
            buyer_email="fullflow@test.com",
        )
        assert "error" not in checkout
        print("\n--- Step 2: Create Checkout ---")
        print(f"Checkout ID: {checkout['checkout_id']}")
        print(f"Status: {checkout['status']}")
        print(f"Subtotal: ${checkout['subtotal'] / 100:.2f}")

        # Step 3: Apply discount
        updated = await ucp_checkout_update(
            merchant_url=integration_server_url,
            checkout_id=checkout["checkout_id"],
            discount_codes=["10OFF"],
        )
        assert "error" not in updated
        print("\n--- Step 3: Apply Discount ---")
        print(f"Discount applied: ${updated['discount_applied'] / 100:.2f}")
        print(f"New total: ${updated['total'] / 100:.2f}")

        # Verify the flow
        assert updated["total"] < checkout["total"]
        print("\n--- Flow Complete ---")
        print(f"Saved ${(checkout['total'] - updated['total']) / 100:.2f} with discount!")
