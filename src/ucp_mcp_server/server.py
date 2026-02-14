"""MCP Server exposing UCP shopping capabilities as tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from .ucp_client import UCPClient, UCPClientError

# Initialize FastMCP server
mcp = FastMCP("ucp-shopping")


@mcp.tool()
async def ucp_discover(merchant_url: str) -> dict[str, Any]:
    """
    Discover a merchant's UCP capabilities and supported payment methods.

    Args:
        merchant_url: The base URL of the UCP-enabled merchant (e.g., http://localhost:8182)

    Returns:
        Dictionary containing:
        - capabilities: List of UCP capabilities the merchant supports
        - payment_handlers: List of payment methods accepted
        - ucp_version: The UCP protocol version
    """
    try:
        async with UCPClient() as client:
            result = await client.discover(merchant_url)
            return {
                "ucp_version": result.ucp_version,
                "capabilities": [
                    {
                        "name": cap.name,
                        "version": cap.version,
                        "spec": cap.spec,
                    }
                    for cap in result.capabilities
                ],
                "payment_handlers": [
                    {
                        "id": h.id,
                        "name": h.name,
                        "version": h.version,
                    }
                    for h in result.payment_handlers
                ],
            }
    except UCPClientError as e:
        return {"error": str(e)}


@mcp.tool()
async def ucp_checkout_create(
    merchant_url: str,
    items: list[dict[str, Any]],
    buyer_name: str,
    buyer_email: str,
    currency: str = "USD",
) -> dict[str, Any]:
    """
    Create a new checkout session with a UCP merchant.

    Args:
        merchant_url: The base URL of the UCP-enabled merchant
        items: List of items to purchase, each with 'id' and 'quantity'
        buyer_name: Full name of the buyer
        buyer_email: Email address of the buyer
        currency: Currency code (default: USD)

    Returns:
        Dictionary containing:
        - checkout_id: The ID of the created checkout session
        - status: Current status of the checkout
        - total: Total amount in smallest currency unit (e.g., cents)
        - line_items: List of items in the cart
    """
    try:
        async with UCPClient() as client:
            result = await client.create_checkout(
                merchant_url=merchant_url,
                items=items,
                buyer={"name": buyer_name, "email": buyer_email},
                currency=currency,
            )
            return {
                "checkout_id": result.id,
                "status": result.status,
                "total": result.total,
                "subtotal": result.subtotal,
                "currency": result.currency,
                "line_items": [
                    {
                        "id": li.item.get("id"),
                        "title": li.item.get("title"),
                        "quantity": li.quantity,
                    }
                    for li in result.line_items
                ],
            }
    except UCPClientError as e:
        return {"error": str(e)}


@mcp.tool()
async def ucp_checkout_complete(
    merchant_url: str,
    checkout_id: str,
    payment_handler_id: str = "mock_payment_handler",
    card_token: str = "success_token",
    card_brand: str = "Visa",
    card_last_digits: str = "4242",
) -> dict[str, Any]:
    """
    Complete a checkout session by submitting payment. This finalizes the purchase.

    Args:
        merchant_url: The base URL of the UCP-enabled merchant
        checkout_id: The ID of the checkout session to complete
        payment_handler_id: The ID of the payment handler to use (from ucp_discover)
        card_token: Payment token from the payment provider
        card_brand: Card brand (e.g., Visa, Mastercard)
        card_last_digits: Last 4 digits of the card

    Returns:
        Dictionary containing:
        - checkout_id: The checkout session ID
        - status: Final status (should be 'complete')
        - total: Final total charged
        - order_id: The order ID for tracking
        - order_url: Permalink to the order
    """
    try:
        async with UCPClient() as client:
            result = await client.complete_checkout(
                merchant_url=merchant_url,
                checkout_id=checkout_id,
                payment_handler_id=payment_handler_id,
                card_token=card_token,
                card_brand=card_brand,
                card_last_digits=card_last_digits,
            )
            response = {
                "checkout_id": result.id,
                "status": result.status,
                "total": result.total,
                "currency": result.currency,
            }
            if result.order:
                response["order_id"] = result.order.id
                response["order_url"] = result.order.permalink_url
            return response
    except UCPClientError as e:
        return {"error": str(e)}


@mcp.tool()
async def ucp_checkout_set_fulfillment(
    merchant_url: str,
    checkout_id: str,
) -> dict[str, Any]:
    """
    Set up shipping/fulfillment for a checkout. Automatically selects the first
    available shipping address and delivery option. Must be called before
    completing checkout if the merchant requires fulfillment.

    Args:
        merchant_url: The base URL of the UCP-enabled merchant
        checkout_id: The ID of the checkout session

    Returns:
        Dictionary containing:
        - checkout_id: The checkout session ID
        - status: Current status
        - total: Updated total (may include shipping costs)
        - fulfillment: Details of selected shipping method
    """
    try:
        async with UCPClient() as client:
            data = await client.setup_fulfillment(
                merchant_url=merchant_url,
                checkout_id=checkout_id,
            )
            return {
                "checkout_id": data["id"],
                "status": data["status"],
                "total": next(
                    (
                        t["amount"]
                        for t in data.get("totals", [])
                        if t["type"] == "total"
                    ),
                    0,
                ),
                "currency": data.get("currency", "USD"),
                "fulfillment": data.get("fulfillment"),
            }
    except UCPClientError as e:
        return {"error": str(e)}


@mcp.tool()
async def ucp_checkout_update(
    merchant_url: str,
    checkout_id: str,
    discount_codes: list[str] | None = None,
) -> dict[str, Any]:
    """
    Update an existing checkout session (e.g., apply discount codes).

    Args:
        merchant_url: The base URL of the UCP-enabled merchant
        checkout_id: The ID of the checkout session to update
        discount_codes: List of discount/promo codes to apply

    Returns:
        Dictionary containing updated checkout information:
        - checkout_id: The checkout session ID
        - status: Current status
        - total: Updated total amount
        - discount_applied: Amount discounted
        - discounts: Details of applied discounts
    """
    try:
        async with UCPClient() as client:
            result = await client.update_checkout(
                merchant_url=merchant_url,
                checkout_id=checkout_id,
                discount_codes=discount_codes,
            )
            return {
                "checkout_id": result.id,
                "status": result.status,
                "total": result.total,
                "subtotal": result.subtotal,
                "discount_applied": result.discount_amount,
                "currency": result.currency,
                "discounts": result.discounts,
            }
    except UCPClientError as e:
        return {"error": str(e)}


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
