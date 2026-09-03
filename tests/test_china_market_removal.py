from fastapi import HTTPException

from api.v1.endpoints.stocks import _validate_and_normalize_stock_code
from src.services.stock_list_parser import ParseStatus, parse_analysis_target
from src.utils.market_review_region import (
    normalize_market_review_region_lenient,
    normalize_market_review_region_strict,
)


def test_parser_rejects_china_market_targets() -> None:
    for code in ("600519", "000001", "00700", "hk00700", "sh000300", "csi930955", "930955.CSI"):
        target = parse_analysis_target(code)
        assert target.asset_type == ParseStatus.UNSUPPORTED
        assert target.unsupported_reason == "china-market targets have been removed"


def test_parser_keeps_non_china_targets() -> None:
    for code in ("AAPL", "TSLA", "7203.T", "005930.KS", "2330.TW"):
        target = parse_analysis_target(code)
        assert target.asset_type == ParseStatus.STOCK


def test_market_review_region_only_keeps_non_china_markets() -> None:
    assert normalize_market_review_region_lenient(None) == "us"
    assert normalize_market_review_region_lenient("both") == "us,jp,kr"
    assert normalize_market_review_region_lenient("cn,us,hk") == "us"
    assert normalize_market_review_region_strict("us,jp") == "us,jp"

    try:
        normalize_market_review_region_strict("cn")
    except ValueError:
        pass
    else:
        raise AssertionError("cn should be rejected from MARKET_REVIEW_REGION")


def test_stocks_api_rejects_china_code_input() -> None:
    try:
        _validate_and_normalize_stock_code("600519")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert isinstance(exc.detail, dict)
        assert exc.detail.get("error") == "invalid_stock_code"
    else:
        raise AssertionError("China stock code should be rejected")

    assert _validate_and_normalize_stock_code("AAPL") == "AAPL"
