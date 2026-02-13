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
