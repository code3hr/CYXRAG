from src.trade_service import TradeRequest, TradeService


def test_approves_valid_trade() -> None:
    service = TradeService(max_amount=1000)
    result = service.approve(TradeRequest("buyer-1", "seller-1", 100, "USD"))

    assert result.approved is True
    assert result.audit_reason == "approved"


def test_rejects_trade_above_limit() -> None:
    service = TradeService(max_amount=1000)
    result = service.approve(TradeRequest("buyer-1", "seller-1", 1500, "USD"))

    assert result.approved is False
    assert result.audit_reason == "limit_exceeded"
