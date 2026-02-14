"""HTTP client for UCP API calls."""

import uuid
from typing import Any

import httpx

from .models import (
    CheckoutSession,
    PaymentHandler,
    UCPCapability,
    UCPDiscoveryResponse,
)


class UCPClientError(Exception):
    """Error from UCP client operations."""

    pass


class UCPClient:
    """Async HTTP client for UCP merchant APIs."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "UCPClient":
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise UCPClientError("Client not initialized. Use async context manager.")
        return self._client

    async def discover(self, merchant_url: str) -> UCPDiscoveryResponse:
        """Discover merchant UCP capabilities."""
        client = self._get_client()
        url = f"{merchant_url.rstrip('/')}/.well-known/ucp"

        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as e:
            raise UCPClientError(f"Could not connect to merchant: {e}")
        except httpx.HTTPStatusError as e:
            raise UCPClientError(f"HTTP error from merchant: {e}")
        except Exception as e:
            raise UCPClientError(f"Error discovering merchant: {e}")

        # Parse the UCP response
        ucp_data = data.get("ucp", {})
        payment_data = data.get("payment", {})

        capabilities = [
            UCPCapability(**cap) for cap in ucp_data.get("capabilities", [])
        ]
        handlers = [PaymentHandler(**h) for h in payment_data.get("handlers", [])]

        return UCPDiscoveryResponse(
            version=ucp_data.get("version", "unknown"),
            capabilities=capabilities,
            payment_handlers=handlers,
        )

    async def create_checkout(
        self,
        merchant_url: str,
        items: list[dict[str, Any]],
        buyer: dict[str, str],
        currency: str = "USD",
        payment_handlers: list[dict] | None = None,
    ) -> CheckoutSession:
        """Create a new checkout session."""
        client = self._get_client()
        url = f"{merchant_url.rstrip('/')}/checkout-sessions"

        # Build line items
        line_items = [
            {
                "item": {"id": item["id"], "title": item.get("title", "")},
                "quantity": item["quantity"],
            }
            for item in items
        ]

        payload = {
            "line_items": line_items,
            "buyer": {
                "full_name": buyer.get("name", ""),
                "email": buyer.get("email", ""),
            },
            "currency": currency,
            "payment": {
                "instruments": [],
                "handlers": payment_handlers or [],
            },
        }

        headers = {
            "Content-Type": "application/json",
            "UCP-Agent": 'profile="https://ucp-mcp-server.example/profile"',
            "request-signature": "test",
            "idempotency-key": str(uuid.uuid4()),
            "request-id": str(uuid.uuid4()),
        }

        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as e:
            raise UCPClientError(f"Could not connect to merchant: {e}")
        except httpx.HTTPStatusError as e:
            raise UCPClientError(
                f"HTTP error from merchant: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise UCPClientError(f"Error creating checkout: {e}")

        return CheckoutSession(**data)

    async def complete_checkout(
        self,
        merchant_url: str,
        checkout_id: str,
        payment_handler_id: str,
        card_token: str = "success_token",
        card_brand: str = "Visa",
        card_last_digits: str = "4242",
    ) -> CheckoutSession:
        """Complete a checkout session by submitting payment."""
        client = self._get_client()
        url = f"{merchant_url.rstrip('/')}/checkout-sessions/{checkout_id}/complete"

        payload = {
            "payment_data": {
                "id": f"instr_{uuid.uuid4().hex[:8]}",
                "handler_id": payment_handler_id,
                "handler_name": payment_handler_id,
                "type": "card",
                "brand": card_brand,
                "last_digits": card_last_digits,
                "credential": {
                    "type": "token",
                    "token": card_token,
                },
                "billing_address": {
                    "street_address": "123 Main St",
                    "address_locality": "Anytown",
                    "address_region": "CA",
                    "address_country": "US",
                    "postal_code": "12345",
                },
            },
            "risk_signals": {
                "ip": "127.0.0.1",
                "browser": "ucp-mcp-server",
            },
        }

        headers = {
            "Content-Type": "application/json",
            "UCP-Agent": 'profile="https://ucp-mcp-server.example/profile"',
            "request-signature": "test",
            "idempotency-key": str(uuid.uuid4()),
            "request-id": str(uuid.uuid4()),
        }

        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as e:
            raise UCPClientError(f"Could not connect to merchant: {e}")
        except httpx.HTTPStatusError as e:
            raise UCPClientError(
                f"HTTP error from merchant: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise UCPClientError(f"Error completing checkout: {e}")

        return CheckoutSession(**data)

    async def get_checkout(
        self,
        merchant_url: str,
        checkout_id: str,
    ) -> dict[str, Any]:
        """Fetch current checkout state."""
        client = self._get_client()
        url = f"{merchant_url.rstrip('/')}/checkout-sessions/{checkout_id}"
        headers = {
            "UCP-Agent": 'profile="https://ucp-mcp-server.example/profile"',
            "request-signature": "test",
            "request-id": str(uuid.uuid4()),
        }
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise UCPClientError(f"Could not connect to merchant: {e}")
        except httpx.HTTPStatusError as e:
            raise UCPClientError(
                f"HTTP error from merchant: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise UCPClientError(f"Error fetching checkout: {e}")

    async def raw_update_checkout(
        self,
        merchant_url: str,
        checkout_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Send a raw update payload to a checkout session."""
        client = self._get_client()
        url = f"{merchant_url.rstrip('/')}/checkout-sessions/{checkout_id}"
        headers = {
            "Content-Type": "application/json",
            "UCP-Agent": 'profile="https://ucp-mcp-server.example/profile"',
            "request-signature": "test",
            "idempotency-key": str(uuid.uuid4()),
            "request-id": str(uuid.uuid4()),
        }
        try:
            response = await client.put(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise UCPClientError(f"Could not connect to merchant: {e}")
        except httpx.HTTPStatusError as e:
            raise UCPClientError(
                f"HTTP error from merchant: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise UCPClientError(f"Error updating checkout: {e}")

    async def setup_fulfillment(
        self,
        merchant_url: str,
        checkout_id: str,
    ) -> dict[str, Any]:
        """Set up fulfillment (shipping) for a checkout. Auto-selects first address and option."""
        # Get current checkout state
        current = await self.get_checkout(merchant_url, checkout_id)

        base_payload = {
            "id": checkout_id,
            "line_items": current["line_items"],
            "currency": current["currency"],
            "payment": current["payment"],
        }

        # Step 1: Trigger fulfillment generation
        payload = {**base_payload, "fulfillment": {"methods": [{"type": "shipping"}]}}
        data = await self.raw_update_checkout(merchant_url, checkout_id, payload)

        # Step 2: Select first destination
        fulfillment = data.get("fulfillment", {})
        methods = fulfillment.get("methods", [])
        if not methods:
            return data

        method = methods[0]
        destinations = method.get("destinations", [])
        if not destinations:
            return data

        dest_id = destinations[0]["id"]
        payload = {
            **base_payload,
            "line_items": data["line_items"],
            "payment": data["payment"],
            "fulfillment": {
                "methods": [{"type": "shipping", "selected_destination_id": dest_id}]
            },
        }
        data = await self.raw_update_checkout(merchant_url, checkout_id, payload)

        # Step 3: Select first shipping option
        fulfillment = data.get("fulfillment", {})
        methods = fulfillment.get("methods", [])
        if not methods:
            return data

        method = methods[0]
        groups = method.get("groups", [])
        if not groups or not groups[0].get("options"):
            return data

        option_id = groups[0]["options"][0]["id"]
        payload = {
            **base_payload,
            "line_items": data["line_items"],
            "payment": data["payment"],
            "fulfillment": {
                "methods": [
                    {
                        "type": "shipping",
                        "selected_destination_id": dest_id,
                        "groups": [{"selected_option_id": option_id}],
                    }
                ]
            },
        }
        data = await self.raw_update_checkout(merchant_url, checkout_id, payload)
        return data

    async def update_checkout(
        self,
        merchant_url: str,
        checkout_id: str,
        discount_codes: list[str] | None = None,
        line_items: list[dict] | None = None,
    ) -> CheckoutSession:
        """Update an existing checkout session."""
        client = self._get_client()
        url = f"{merchant_url.rstrip('/')}/checkout-sessions/{checkout_id}"

        # First, fetch the current checkout state so we can send required fields
        get_headers = {
            "UCP-Agent": 'profile="https://ucp-mcp-server.example/profile"',
            "request-signature": "test",
            "request-id": str(uuid.uuid4()),
        }
        try:
            get_response = await client.get(url, headers=get_headers)
            get_response.raise_for_status()
            current = get_response.json()
        except Exception:
            # If we can't fetch, build a minimal payload
            current = {}

        payload: dict[str, Any] = {"id": checkout_id}

        # Include required fields from current checkout state
        if current.get("line_items"):
            payload["line_items"] = current["line_items"]
        if line_items:
            payload["line_items"] = line_items

        payload["currency"] = current.get("currency", "USD")
        payload["payment"] = current.get("payment", {"instruments": [], "handlers": []})

        if discount_codes:
            payload["discounts"] = {"codes": discount_codes}

        headers = {
            "Content-Type": "application/json",
            "UCP-Agent": 'profile="https://ucp-mcp-server.example/profile"',
            "request-signature": "test",
            "idempotency-key": str(uuid.uuid4()),
            "request-id": str(uuid.uuid4()),
        }

        try:
            response = await client.put(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as e:
            raise UCPClientError(f"Could not connect to merchant: {e}")
        except httpx.HTTPStatusError as e:
            raise UCPClientError(
                f"HTTP error from merchant: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise UCPClientError(f"Error updating checkout: {e}")

        return CheckoutSession(**data)
