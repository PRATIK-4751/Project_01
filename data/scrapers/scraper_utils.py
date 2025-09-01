import pandas as pd
from .serpapi_google_shopping import search_google_shopping

def scrape_multiple_sources(query: str) -> pd.DataFrame:
    """Scrape from multiple sources simultaneously"""
    df = search_google_shopping(query)
    
    if not df.empty:
        df['price_inr'] = df['price_inr'] 
        return df.sort_values('price_inr')
    
    return pd.DataFrame()
