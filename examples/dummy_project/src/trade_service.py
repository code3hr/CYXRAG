"""Small trade approval example used by Open RAG documentation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TradeRequest:
    buyer_id: str
    seller_id: str
    amount: float
    currency: str


@dataclass(frozen=True)
class ApprovalResult:
    approved: bool
    reason: str
    audit_reason: str


class TradeService:
    def __init__(self, max_amount: float = 1000.0) -> None:
        self.max_amount = max_amount

    def approve(self, request: TradeRequest) -> ApprovalResult:
        if not request.buyer_id:
            return ApprovalResult(False, "Buyer is required.", "missing_buyer")
        if not request.seller_id:
            return ApprovalResult(False, "Seller is required.", "missing_seller")
        if request.amount <= 0:
            return ApprovalResult(False, "Amount must be positive.", "invalid_amount")
        if request.amount > self.max_amount:
            return ApprovalResult(False, "Amount is above the trade limit.", "limit_exceeded")
        return ApprovalResult(True, "Trade approved.", "approved")
