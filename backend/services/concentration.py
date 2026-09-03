import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel

class SectorWeightItem(BaseModel):
    sector: str
    market_value: float
    weight_pct: float
    holdings_count: int

class HHIAnalysisResponse(BaseModel):
    hhi_score: float
    concentration_level: str # 'Well Diversified', 'Moderately Concentrated', 'Highly Concentrated'
    interpretation: str
    total_portfolio_value: float
    sector_breakdown: List[SectorWeightItem]
    top_concentrated_sector: str
    top_sector_weight_pct: float

def compute_hhi(holdings: List[Dict[str, Any]]) -> HHIAnalysisResponse:
    """
    Computes Herfindahl-Hirschman Index (HHI) for sector concentration:
    HHI = sum( (weight_i * 100)^2 ) across sectors, scaled 0 to 10000.
    
    Bands:
    - < 1500: Well Diversified (low concentration risk)
    - 1500 - 2500: Moderately Concentrated (balanced risk across 4-6 key sectors)
    - > 2500: Highly Concentrated (vulnerable to sector-specific shocks)
    """
    if not holdings:
        return HHIAnalysisResponse(
            hhi_score=0.0,
            concentration_level="No Holdings",
            interpretation="Your portfolio currently has no active holdings. Add assets to analyze concentration.",
            total_portfolio_value=0.0,
            sector_breakdown=[],
            top_concentrated_sector="None",
            top_sector_weight_pct=0.0
        )
    
    df = pd.DataFrame(holdings)
    
    # Calculate market value if not present
    if "current_value" not in df.columns:
        df["current_value"] = df["quantity"] * df["current_price"]
        
    total_val = float(df["current_value"].sum())
    if total_val <= 0:
        return HHIAnalysisResponse(
            hhi_score=0.0,
            concentration_level="Zero Value",
            interpretation="Portfolio market value is zero.",
            total_portfolio_value=0.0,
            sector_breakdown=[],
            top_concentrated_sector="None",
            top_sector_weight_pct=0.0
        )
        
    # Group by sector
    sector_grp = df.groupby("sector").agg(
        market_value=("current_value", "sum"),
        holdings_count=("ticker", "count")
    ).reset_index()
    
    sector_grp["weight_pct"] = (sector_grp["market_value"] / total_val) * 100.0
    
    # Calculate HHI
    # HHI = sum((weight_pct)^2)
    hhi_score = float(np.sum(sector_grp["weight_pct"] ** 2))
    hhi_score = round(hhi_score, 2)
    
    # Sort sectors by weight descending
    sector_grp = sector_grp.sort_values(by="weight_pct", ascending=False)
    
    top_row = sector_grp.iloc[0]
    top_sector = str(top_row["sector"])
    top_weight = round(float(top_row["weight_pct"]), 2)
    
    # Translate to plain-language label
    if hhi_score < 1500:
        level = "Well Diversified"
        desc = (
            f"Your portfolio is well diversified with an HHI score of {hhi_score:.0f}. "
            f"Capital is distributed across {len(sector_grp)} sectors, with top sector '{top_sector}' "
            f"accounting for {top_weight}% of total value, mitigating single-sector systemic exposure."
        )
    elif 1500 <= hhi_score <= 2500:
        level = "Moderately Concentrated"
        desc = (
            f"Your portfolio is moderately concentrated with an HHI score of {hhi_score:.0f}. "
            f"The '{top_sector}' sector holds {top_weight}% of total portfolio value. "
            f"Consider monitoring cross-sector correlations to ensure balance across market cycles."
        )
    else:
        level = "Highly Concentrated"
        desc = (
            f"Your portfolio is highly concentrated with an HHI score of {hhi_score:.0f} (> 2500). "
            f"The top sector '{top_sector}' dominates {top_weight}% of total capital. "
            f"Macroeconomic volatility impacting this sector will disproportionately affect overall portfolio variance."
        )
        
    sector_items = [
        SectorWeightItem(
            sector=str(r["sector"]),
            market_value=round(float(r["market_value"]), 2),
            weight_pct=round(float(r["weight_pct"]), 2),
            holdings_count=int(r["holdings_count"])
        )
        for _, r in sector_grp.iterrows()
    ]
    
    return HHIAnalysisResponse(
        hhi_score=hhi_score,
        concentration_level=level,
        interpretation=desc,
        total_portfolio_value=round(total_val, 2),
        sector_breakdown=sector_items,
        top_concentrated_sector=top_sector,
        top_sector_weight_pct=top_weight
    )
