import pandas as pd
from .serpapi_google_shopping import search_google_shopping

def scrape_multiple_sources(query: str) -> pd.DataFrame:
    """Scrape from multiple sources simultaneously"""
    df = search_google_shopping(query)
    
    if not df.empty:
        return df.sort_values('price_value')
    
    return pd.DataFrame()
