
def make_brief(trade: dict) -> dict:
    title = f"{trade.get('transaction_type','').upper()} {trade.get('ticker') or trade.get('issuer') or ''}"
    why = "Potential alignment with committee interests; watch for sector-wide moves."
    text = f"**{title}** by {trade.get('official_name')} on {trade.get('trade_date')}. {why}"
    return {"text": text, "citations": [trade.get("filing_url","")]}
