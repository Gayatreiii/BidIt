from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import json

from backend.api.auth import get_current_user_id
from backend.database import get_db_connection
from backend.services.concentration import compute_hhi, HHIAnalysisResponse
from backend.models.gat_risk_model import risk_engine
from backend.api.portfolio import get_user_holdings

router = APIRouter(prefix="/api/analytics", tags=["Portfolio Analytics & Cross-Sector Risk"])

@router.get("/concentration", response_model=HHIAnalysisResponse)
def get_portfolio_concentration(user_id: str = Depends(get_current_user_id)):
    """
    Module 3: Computes sector-wise weightage and Herfindahl-Hirschman Index (HHI).
    Translates score to plain-language concentration bands.
    """
    holdings_resp = get_user_holdings(user_id=user_id)
    holdings_dicts = [h.model_dump() for h in holdings_resp]
    return compute_hhi(holdings_dicts)

@router.get("/cross-sector-risk")
def get_cross_sector_risk_propagation(user_id: str = Depends(get_current_user_id)):
    """
    Module 4: Runs Graph Attention Network (GAT) in PyTorch Geometric to estimate
    attention-weighted volatility shock propagation across sectors and surfaces
    plain-language, strictly descriptive risk alerts.
    """
    # 1. Get user's current sector weights
    holdings_resp = get_user_holdings(user_id=user_id)
    holdings_dicts = [h.model_dump() for h in holdings_resp]
    hhi_analysis = compute_hhi(holdings_dicts)
    
    sector_weights = {
        s.sector: s.weight_pct for s in hhi_analysis.sector_breakdown
    }
    
    # 2. Run GAT model inference
    gat_result = risk_engine.compute_risk_propagation(user_sector_weights=sector_weights)
    return {
        "hhi_summary": {
            "score": hhi_analysis.hhi_score,
            "level": hhi_analysis.concentration_level,
            "top_sector": hhi_analysis.top_concentrated_sector,
            "top_sector_weight_pct": hhi_analysis.top_sector_weight_pct
        },
        "gat_risk_model": gat_result
    }

@router.get("/gat-backtest")
def get_gat_backtest_report():
    """
    Module 4 Deliverable: Quantitative backtest report evaluating GAT shock propagation
    accuracy and MAE against historical Indian equity sector volatility windows.
    """
    return risk_engine.run_historical_backtest()
