import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.concentration import compute_hhi
from backend.models.gat_risk_model import risk_engine

client = TestClient(app)

def test_module_3_hhi_concentration():
    # 1. Test balanced portfolio
    balanced_holdings = [
        {"ticker": "TCS.NS", "sector": "IT", "quantity": 10, "current_price": 4000.0, "current_value": 40000.0},
        {"ticker": "HDFCBANK.NS", "sector": "Financial Services", "quantity": 25, "current_price": 1600.0, "current_value": 40000.0},
        {"ticker": "RELIANCE.NS", "sector": "Energy", "quantity": 15, "current_price": 2800.0, "current_value": 42000.0},
        {"ticker": "TATAMOTORS.NS", "sector": "Automobile", "quantity": 40, "current_price": 1000.0, "current_value": 40000.0},
        {"ticker": "SUNPHARMA.NS", "sector": "Pharma", "quantity": 25, "current_price": 1600.0, "current_value": 40000.0},
    ]
    balanced_res = compute_hhi(balanced_holdings)
    assert balanced_res.hhi_score < 2500
    assert balanced_res.concentration_level in ["Well Diversified", "Moderately Concentrated"]
    assert len(balanced_res.sector_breakdown) == 5

    # 2. Test highly concentrated single-sector portfolio
    concentrated_holdings = [
        {"ticker": "TCS.NS", "sector": "IT", "quantity": 20, "current_price": 4000.0, "current_value": 80000.0},
        {"ticker": "INFY.NS", "sector": "IT", "quantity": 40, "current_price": 1800.0, "current_value": 72000.0},
    ]
    conc_res = compute_hhi(concentrated_holdings)
    assert conc_res.hhi_score == 10000.0
    assert conc_res.concentration_level == "Highly Concentrated"
    assert "dominated" in conc_res.interpretation.lower() or "highly concentrated" in conc_res.interpretation.lower()

def test_module_4_gat_inference_and_alerts():
    # User holds 50% Energy and 50% Financial Services
    user_weights = {
        "Energy": 50.0,
        "Financial Services": 50.0
    }
    result = risk_engine.compute_risk_propagation(user_weights)
    
    assert "sectors" in result
    assert len(result["sectors"]) == 9
    assert "correlation_matrix" in result
    assert "active_risk_alerts" in result
    
    # Check that model returns descriptive alerts without buy/sell advice
    alerts = result["active_risk_alerts"]
    assert len(alerts) > 0
    for alert in alerts:
        desc = alert["descriptive_signal"]
        assert "correlation" in desc.lower()
        # Verify strict compliance constraint: no directive advice
        assert "you should buy" not in desc.lower()
        assert "you should sell" not in desc.lower()

def test_module_4_historical_backtesting():
    backtest = risk_engine.run_historical_backtest()
    assert backtest["total_backtest_windows"] == 6
    assert backtest["directional_accuracy_pct"] >= 80.0
    assert backtest["mean_absolute_error"] < 0.10
    assert "N=6" in backtest["sample_size_label"]
    assert "6/6" in backtest["directional_agreement_ratio"]
    assert len(backtest["caveats"]) >= 3
    assert any("Indian equity" in c for c in backtest["caveats"])
    assert any("sample size" in c.lower() for c in backtest["caveats"])

def test_analytics_endpoints_authenticated():
    # Signup user
    signup_payload = {
        "email": "analytics_test@bidup.ai",
        "password": "Password123!",
        "display_name": "Analytics Tester",
        "risk_tolerance": "medium",
        "investment_horizon": "medium",
        "sector_exclusions": []
    }
    client.post("/api/auth/signup", json=signup_payload)
    login_res = client.post("/api/auth/login", json={"email": "analytics_test@bidup.ai", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add holding
    client.post("/api/portfolio/manual", json={"ticker": "TCS.NS", "quantity": 10, "avg_buy_price": 4000.0}, headers=headers)
    client.post("/api/portfolio/manual", json={"ticker": "RELIANCE.NS", "quantity": 15, "avg_buy_price": 2900.0}, headers=headers)

    # Test /api/analytics/concentration
    res_conc = client.get("/api/analytics/concentration", headers=headers)
    assert res_conc.status_code == 200
    data_conc = res_conc.json()
    assert data_conc["hhi_score"] > 0
    assert len(data_conc["sector_breakdown"]) == 2

    # Test /api/analytics/cross-sector-risk
    res_risk = client.get("/api/analytics/cross-sector-risk", headers=headers)
    assert res_risk.status_code == 200
    data_risk = res_risk.json()
    assert "gat_risk_model" in data_risk
    assert len(data_risk["gat_risk_model"]["sectors"]) == 9

    # Test /api/analytics/gat-backtest
    res_bt = client.get("/api/analytics/gat-backtest")
    assert res_bt.status_code == 200
    assert res_bt.json()["directional_accuracy_pct"] > 80.0

if __name__ == "__main__":
    pytest.main(["-v", __file__])
