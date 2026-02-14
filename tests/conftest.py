"""Pytest fixtures for UCP MCP Server tests."""

import pytest
import respx
from httpx import Response


def pytest_addoption(parser):
    """Add command line option to run integration tests."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests against live UCP server",
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration is passed."""
    if config.getoption("--run-integration"):
        # Run integration tests
        return

    skip_integration = pytest.mark.skip(reason="Need --run-integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


# Sample UCP discovery response (based on flower shop example)
SAMPLE_DISCOVERY_RESPONSE = {
    "ucp": {
        "version": "2026-01-11",
        "services": {
            "dev.ucp.shopping": {
                "version": "2026-01-11",
                "spec": "https://ucp.dev/specs/shopping",
                "rest": {
                    "schema": "https://ucp.dev/services/shopping/openapi.json",
                    "endpoint": "http://localhost:8182/",
                },
            }
        },
        "capabilities": [
            {
                "name": "dev.ucp.shopping.checkout",
                "version": "2026-01-11",
                "spec": "https://ucp.dev/specs/shopping/checkout",
                "schema": "https://ucp.dev/schemas/shopping/checkout.json",
            },
            {
                "name": "dev.ucp.shopping.discount",
                "version": "2026-01-11",
                "spec": "https://ucp.dev/specs/shopping/discount",
                "schema": "https://ucp.dev/schemas/shopping/discount.json",
                "extends": "dev.ucp.shopping.checkout",
            },
            {
                "name": "dev.ucp.shopping.fulfillment",
                "version": "2026-01-11",
                "spec": "https://ucp.dev/specs/shopping/fulfillment",
                "schema": "https://ucp.dev/schemas/shopping/fulfillment.json",
                "extends": "dev.ucp.shopping.checkout",
            },
        ],
    },
    "payment": {
        "handlers": [
            {
                "id": "shop_pay",
                "name": "com.shopify.shop_pay",
                "version": "2026-01-11",
                "spec": "https://shopify.dev/ucp/handlers/shop_pay",
                "config_schema": "https://shopify.dev/ucp/handlers/shop_pay/config.json",
                "instrument_schemas": [
                    "https://shopify.dev/ucp/handlers/shop_pay/instrument.json"
                ],
                "config": {"shop_id": "d124d01c-3386-4c58-bc58-671b705e19ff"},
            },
            {
                "id": "google_pay",
                "name": "google.pay",
                "version": "2026-01-11",
                "spec": "https://example.com/spec",
                "config_schema": "https://example.com/schema",
                "instrument_schemas": [
                    "https://ucp.dev/schemas/shopping/types/gpay_card_payment_instrument.json"
                ],
                "config": {
                    "api_version": 2,
                    "merchant_info": {"merchant_name": "Flower Shop"},
                },
            },
        ]
    },
}

# Sample checkout session response
SAMPLE_CHECKOUT_RESPONSE = {
    "ucp": {
        "version": "2026-01-11",
        "capabilities": [
            {"name": "dev.ucp.shopping.checkout", "version": "2026-01-11"}
        ],
    },
    "id": "cb9c0fc5-3e81-427c-ae54-83578294daf3",
    "line_items": [
        {
            "id": "2e86d63a-a6b8-4b4d-8f41-559f4c6991ea",
            "item": {
                "id": "bouquet_roses",
                "title": "Bouquet of Red Roses",
                "price": 3500,
            },
            "quantity": 1,
            "totals": [
                {"type": "subtotal", "amount": 3500},
                {"type": "total", "amount": 3500},
            ],
        }
    ],
    "buyer": {"full_name": "John Doe", "email": "john.doe@example.com"},
    "status": "ready_for_complete",
    "currency": "USD",
    "totals": [
        {"type": "subtotal", "amount": 3500},
        {"type": "total", "amount": 3500},
    ],
    "links": [],
    "payment": {"handlers": [], "instruments": []},
    "discounts": {},
}

# Sample checkout with discount applied
SAMPLE_CHECKOUT_WITH_DISCOUNT = {
    "ucp": {
        "version": "2026-01-11",
        "capabilities": [
            {"name": "dev.ucp.shopping.checkout", "version": "2026-01-11"}
        ],
    },
    "id": "cb9c0fc5-3e81-427c-ae54-83578294daf3",
    "line_items": [
        {
            "id": "2e86d63a-a6b8-4b4d-8f41-559f4c6991ea",
            "item": {
                "id": "bouquet_roses",
                "title": "Bouquet of Red Roses",
                "price": 3500,
            },
            "quantity": 1,
            "totals": [
                {"type": "subtotal", "amount": 3500},
                {"type": "total", "amount": 3500},
            ],
        }
    ],
    "buyer": {"full_name": "John Doe", "email": "john.doe@example.com"},
    "status": "ready_for_complete",
    "currency": "USD",
    "totals": [
        {"type": "subtotal", "amount": 3500},
        {"type": "discount", "amount": 350},
        {"type": "total", "amount": 3150},
    ],
    "links": [],
    "payment": {"handlers": [], "instruments": []},
    "discounts": {
        "codes": ["10OFF"],
        "applied": [
            {
                "code": "10OFF",
                "title": "10% Off",
                "amount": 350,
                "automatic": False,
                "allocations": [{"path": "subtotal", "amount": 350}],
            }
        ],
    },
}

# Sample completed checkout response
SAMPLE_CHECKOUT_COMPLETED = {
    "ucp": {
        "version": "2026-01-11",
        "capabilities": [
            {"name": "dev.ucp.shopping.checkout", "version": "2026-01-11"}
        ],
    },
    "id": "cb9c0fc5-3e81-427c-ae54-83578294daf3",
    "line_items": [
        {
            "id": "2e86d63a-a6b8-4b4d-8f41-559f4c6991ea",
            "item": {
                "id": "bouquet_roses",
                "title": "Bouquet of Red Roses",
                "price": 3500,
            },
            "quantity": 1,
            "totals": [
                {"type": "subtotal", "amount": 3500},
                {"type": "total", "amount": 3500},
            ],
        }
    ],
    "buyer": {"full_name": "John Doe", "email": "john.doe@example.com"},
    "status": "complete",
    "currency": "USD",
    "totals": [
        {"type": "subtotal", "amount": 3500},
        {"type": "total", "amount": 3500},
    ],
    "links": [],
    "payment": {"handlers": [], "instruments": []},
    "discounts": {},
    "order": {
        "id": "order-abc-123",
        "permalink_url": "http://localhost:8182/orders/order-abc-123",
    },
}


@pytest.fixture
def mock_ucp_server():
    """Fixture that mocks UCP server responses."""
    with respx.mock(assert_all_called=False) as respx_mock:
        # Discovery endpoint
        respx_mock.get("http://localhost:8182/.well-known/ucp").mock(
            return_value=Response(200, json=SAMPLE_DISCOVERY_RESPONSE)
        )

        # Create checkout endpoint
        respx_mock.post("http://localhost:8182/checkout-sessions").mock(
            return_value=Response(200, json=SAMPLE_CHECKOUT_RESPONSE)
        )

        # Get checkout endpoint (for update flow)
        respx_mock.get(url__regex=r"http://localhost:8182/checkout-sessions/.*").mock(
            return_value=Response(200, json=SAMPLE_CHECKOUT_RESPONSE)
        )

        # Update checkout endpoint
        respx_mock.put(url__regex=r"http://localhost:8182/checkout-sessions/.*").mock(
            return_value=Response(200, json=SAMPLE_CHECKOUT_WITH_DISCOUNT)
        )

        # Complete checkout endpoint
        respx_mock.post(
            url__regex=r"http://localhost:8182/checkout-sessions/.*/complete"
        ).mock(return_value=Response(200, json=SAMPLE_CHECKOUT_COMPLETED))

        yield respx_mock


@pytest.fixture
def mock_invalid_server():
    """Fixture that simulates connection failures."""
    with respx.mock(assert_all_called=False) as respx_mock:
        import httpx

        respx_mock.get("http://invalid.example/.well-known/ucp").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        yield respx_mock
