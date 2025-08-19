
from typing import List, Optional, Dict, Any
def backtest_equal_weight(trades: List[dict], hold_days: int = 30, benchmark: str = "SPY",
                          chamber: Optional[str]=None, tx_filter: Optional[str]=None,
                          start_date=None, end_date=None, sectors: Optional[list]=None) -> Dict[str, Any]:
    # Demo output
    return {
        "summary": {"alpha": 0.07, "sharpe": 1.2, "beta": 0.8, "idio_vol": 0.15},
        "top_holdings": [{"ticker":"AAPL","trades":12,"avg_return":0.04},{"ticker":"MSFT","trades":9,"avg_return":0.03}],
        "sector_breakdown": [{"sector":"Technology","pct":0.62},{"sector":"Energy","pct":0.18},{"sector":"Unknown","pct":0.20}]
    }
