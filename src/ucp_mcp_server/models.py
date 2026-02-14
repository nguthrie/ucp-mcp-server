"""Pydantic models for UCP requests and responses."""

from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Discovery Models
# ============================================================================


class UCPCapability(BaseModel):
    """A UCP capability declared by a merchant."""

    name: str
    version: str
    spec: str | None = None
    schema_url: str | None = Field(None, alias="schema")
    extends: str | None = None


class PaymentHandler(BaseModel):
    """A payment handler supported by a merchant."""

    id: str
    name: str
    version: str
    spec: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class UCPDiscoveryResponse(BaseModel):
    """Response from /.well-known/ucp endpoint."""

    ucp_version: str = Field(alias="version")
    capabilities: list[UCPCapability] = Field(default_factory=list)
    payment_handlers: list[PaymentHandler] = Field(default_factory=list)


# ============================================================================
# Checkout Models
# ============================================================================


class LineItem(BaseModel):
    """An item in a checkout."""

    id: str | None = None
    item: dict[str, Any]
    quantity: int
    totals: list[dict[str, Any]] = Field(default_factory=list)


class CheckoutTotals(BaseModel):
    """Totals for a checkout."""

    type: str
    amount: int


class DiscountApplied(BaseModel):
    """A discount that was applied."""

    code: str
    title: str | None = None
    amount: int
    automatic: bool = False


class OrderInfo(BaseModel):
    """Order information returned after checkout completion."""

    id: str | None = None
    permalink_url: str | None = None


class CheckoutSession(BaseModel):
    """A UCP checkout session."""

    id: str
    status: str
    currency: str = "USD"
    line_items: list[LineItem] = Field(default_factory=list)
    totals: list[CheckoutTotals] = Field(default_factory=list)
    discounts: dict[str, Any] = Field(default_factory=dict)
    order: OrderInfo | None = Field(default=None)

    @property
    def total(self) -> int:
        """Get the total amount."""
        for t in self.totals:
            if t.type == "total":
                return t.amount
        return 0

    @property
    def subtotal(self) -> int:
        """Get the subtotal amount."""
        for t in self.totals:
            if t.type == "subtotal":
                return t.amount
        return 0

    @property
    def discount_amount(self) -> int:
        """Get the discount amount."""
        for t in self.totals:
            if t.type == "discount":
                return t.amount
        return 0


# ============================================================================
# Request Models (for MCP tool inputs)
# ============================================================================


class DiscoverRequest(BaseModel):
    """Request to discover merchant capabilities."""

    merchant_url: str


class CheckoutItem(BaseModel):
    """An item to add to checkout."""

    id: str
    quantity: int = 1


class BuyerInfo(BaseModel):
    """Buyer information for checkout."""

    name: str
    email: str


class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session."""

    merchant_url: str
    items: list[CheckoutItem]
    buyer: BuyerInfo
    currency: str = "USD"


class UpdateCheckoutRequest(BaseModel):
    """Request to update a checkout session (e.g., apply discount)."""

    merchant_url: str
    checkout_id: str
    discount_codes: list[str] = Field(default_factory=list)
