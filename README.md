# ucp-mcp-server

**Let AI assistants shop.** An MCP server that gives Claude, Cursor, and any MCP-compatible AI the ability to interact with UCP-enabled merchants.

> **UCP** (Universal Commerce Protocol) is Google's new open standard for agentic commerce, backed by Shopify, Stripe, Visa, Mastercard, Target, Walmart, and 20+ partners.
>
> **MCP** (Model Context Protocol) is the standard for giving AI assistants access to tools.
>
> This project connects them.

---

## What Can It Do?

| Tool | Description |
|------|-------------|
| `ucp_discover` | Find out what a merchant supports (capabilities, payment methods) |
| `ucp_checkout_create` | Start a purchase (add items to cart, set buyer info) |
| `ucp_checkout_update` | Apply discount codes to an existing checkout |
| `ucp_checkout_set_fulfillment` | Set up shipping (auto-selects address and delivery option) |
| `ucp_checkout_complete` | Complete the purchase by submitting payment |

Your AI assistant gets structured, type-safe access to the entire UCP shopping flow. No scraping, no browser automation, no brittle hacks.

## Quick Start

### Install

```bash
pip install ucp-mcp-server
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install ucp-mcp-server
```

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ucp-shopping": {
      "command": "ucp-mcp-server"
    }
  }
}
```

### Use with Cursor

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ucp-shopping": {
      "command": "ucp-mcp-server"
    }
  }
}
```

### Run Directly

```bash
# As a module
python -m ucp_mcp_server

# Or via the entry point
ucp-mcp-server
```

## Tools Reference

### `ucp_discover`

Discover what a UCP merchant supports before shopping.

```
Arguments:
  merchant_url (str): Base URL of a UCP-enabled merchant

Returns:
  capabilities: List of supported UCP capabilities (checkout, discount, fulfillment)
  payment_handlers: Accepted payment methods (Shop Pay, Google Pay, etc.)
  ucp_version: Protocol version the merchant implements
```

### `ucp_checkout_create`

Create a new shopping cart / checkout session.

```
Arguments:
  merchant_url (str): Base URL of the merchant
  items (list): Items to buy, each with "id" and "quantity"
  buyer_name (str): Full name of the buyer
  buyer_email (str): Email address
  currency (str): Currency code (default: "USD")

Returns:
  checkout_id: Session ID for tracking this purchase
  status: Current checkout status
  total: Total price in smallest currency unit (cents)
  subtotal: Subtotal before discounts
  line_items: What's in the cart
```

### `ucp_checkout_update`

Apply discount codes or modify an existing checkout.

```
Arguments:
  merchant_url (str): Base URL of the merchant
  checkout_id (str): The checkout session to update
  discount_codes (list[str]): Promo codes to apply

Returns:
  checkout_id: Session ID
  total: Updated total after discounts
  discount_applied: How much was saved
  discounts: Details of applied discounts
```

### `ucp_checkout_set_fulfillment`

Set up shipping for a checkout. Automatically selects the first available address and delivery option.

```
Arguments:
  merchant_url (str): Base URL of the merchant
  checkout_id (str): The checkout session

Returns:
  checkout_id: Session ID
  status: Current status
  total: Updated total (may include shipping costs)
  fulfillment: Details of selected shipping method
```

### `ucp_checkout_complete`

Complete a checkout by submitting payment. This finalizes the purchase and returns an order ID.

```
Arguments:
  merchant_url (str): Base URL of the merchant
  checkout_id (str): The checkout session to complete
  payment_handler_id (str): Payment handler to use (from ucp_discover)
  card_token (str): Payment token from the provider
  card_brand (str): Card brand (e.g., "Visa")
  card_last_digits (str): Last 4 digits of the card

Returns:
  checkout_id: Session ID
  status: "complete" or "completed"
  total: Final amount charged
  order_id: Order ID for tracking
  order_url: Permalink to the order
```

## Example Conversation

> **You:** "Find out what the flower shop at http://flowers.example.com supports"
>
> **Claude:** *calls ucp_discover* "This merchant supports checkout, discounts, and fulfillment tracking. They accept Shop Pay and Google Pay."
>
> **You:** "Buy 2 bouquets of roses for me"
>
> **Claude:** *calls ucp_checkout_create* "I've created a checkout for 2 Bouquet of Red Roses. Total: $70.00. Would you like to proceed?"
>
> **You:** "Try the code 10OFF first"
>
> **Claude:** *calls ucp_checkout_update* "Applied 10OFF - saved $7.00! New total: $63.00."

## Why This Exists

Every AI app is going to need shopping capabilities. UCP standardizes how merchants expose commerce APIs. MCP standardizes how AI assistants use tools. This project is the bridge.

Without this, connecting AI to commerce means:
- Scraping websites (brittle, breaks constantly)
- Building custom integrations per merchant (doesn't scale)
- Browser automation (slow, unreliable, expensive)

With UCP + MCP:
- One protocol, every merchant
- Structured data in, structured data out
- Works with any MCP-compatible AI assistant

## Development

```bash
# Clone the repo
git clone https://github.com/nguthrie/ucp-mcp-server.git
cd ucp-mcp-server

# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest -v

# Run integration tests (requires a live UCP server on port 8182)
uv run pytest -v -m integration --run-integration
```

### Project Structure

```
ucp-mcp-server/
├── src/ucp_mcp_server/
│   ├── __init__.py        # Package version
│   ├── __main__.py        # python -m entry point
│   ├── server.py          # MCP server + tool definitions
│   ├── ucp_client.py      # HTTP client for UCP APIs
│   └── models.py          # Pydantic models for UCP data
└── tests/
    ├── conftest.py         # Test fixtures with mock UCP responses
    ├── test_discovery.py   # Discovery tool tests
    ├── test_checkout.py    # Checkout tool tests
    ├── test_errors.py      # Error handling tests
    └── test_integration.py # Live server integration tests
```

## Roadmap

- [x] Merchant capability discovery
- [x] Checkout session creation
- [x] Discount code application
- [x] Fulfillment / shipping setup
- [x] Purchase completion / payment submission
- [ ] Order fulfillment tracking
- [ ] Returns and exchanges
- [ ] Multi-merchant comparison shopping
- [ ] Hosted managed version (so you don't have to self-host)

## Resources

- [UCP Specification](https://ucp.dev) - The Universal Commerce Protocol
- [UCP GitHub](https://github.com/universal-commerce-protocol/ucp)
- [UCP Python SDK](https://github.com/Universal-Commerce-Protocol/python-sdk)
- [MCP Documentation](https://modelcontextprotocol.io) - Model Context Protocol
- [Google's UCP Blog Post](https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/)

## License

MIT
