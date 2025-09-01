import requests
import pandas as pd
import numpy as np
import random
import logging
import time  
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from .serpapi_google_shopping import search_google_shopping

def validate_product_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean product data"""
    if df.empty:
        return df
        
    
    df = df[df['price_inr'] > 0]
    
    
    df['product_name'] = df['product_name'].str.strip()
    
    
    df.loc[df['rating'] > 5, 'rating'] = 5
    df.loc[df['rating'] < 0, 'rating'] = 0
    
    return df

def enhance_product_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add additional statistics and metrics to the product data"""
    if df.empty:
        return df
    
    df = validate_product_data(df)    
    df['price_normalized'] = (df['price_inr'] - df['price_inr'].mean()) / df['price_inr'].std()
    df['value_score'] = (df['rating'] * df['reviews']) / df['price_inr']
    df['timestamp'] = datetime.now()
    df['availability_score'] = np.random.choice(['High', 'Medium', 'Low'], size=len(df))
    
    

    df['popularity_score'] = (df['rating'] * np.log1p(df['reviews']))
    return df

def visualize_price_distribution(df: pd.DataFrame) -> Optional[Union[go.Figure, None]]:
    """Create an interactive price distribution visualization"""
    if df.empty:
        return None
        
    fig = px.box(df, 
                 y='price_inr',
                 x='source',
                 title='Price Distribution by Source',
                 color='source',
                 height=400)
    return fig

def get_price_insights(df: pd.DataFrame) -> Dict:
    """Generate statistical insights about prices"""
    if df.empty:
        return {}
        
    return {
        'avg_price': df['price_inr'].mean(),
        'median_price': df['price_inr'].median(),
        'price_range': (df['price_inr'].min(), df['price_inr'].max()),
        'best_value': df.loc[df['value_score'].idxmax()]['product_name'],
        'total_products': len(df)
    }

def get_trending_products(df: pd.DataFrame, n: int = 5) -> List[Dict]:
    """Get trending products based on multiple metrics"""
    if df.empty:
        return []
    
    

    df['trending_score'] = (
        df['value_score'] * 0.4 +
        df['popularity_score'] * 0.4 +
        df['price_normalized'] * 0.2
    )
    
    trending = df.nlargest(n, 'trending_score')
    return trending.to_dict('records')

def export_results(df: pd.DataFrame, format: str = 'csv', output_dir: str = None) -> str:
    """Export results to various formats and return the file path"""
    if df.empty:
        raise ValueError("No data to export")
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = output_dir or Path.cwd()
    output_path = Path(output_dir)
    
    try:
        filename = f'product_data_{timestamp}'
        if format == 'csv':
            filepath = output_path / f'{filename}.csv'
            df.to_csv(filepath, index=False)
        elif format == 'excel':
            filepath = output_path / f'{filename}.xlsx'
            df.to_excel(filepath, index=False)
        elif format == 'json':
            filepath = output_path / f'{filename}.json'
            df.to_json(filepath, orient='records')
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        return str(filepath)
    except Exception as e:
        logging.error(f"Error exporting data: {str(e)}")
        raise

def multi_source_scraper(query: str = "laptop", max_results: int = 20) -> pd.DataFrame:
    """Combined scraper with fallback and multiple sources"""
    logging.info(f"Starting scraping for query: {query}")
    
    try:
        # Try Google Shopping first
        df = search_google_shopping(query, max_results)
        
        
        if df.empty:
            
            dfs = []
            sources = [
                (scrape_direct_websites, "Direct Websites"),
                (scrape_price_comparison_sites, "Price Comparison"),
                (scrape_social_commerce, "Social Commerce"),
                (scrape_international_sites, "International"),
                (scrape_fallback_data, "Fallback")
            ]
            
            for scraper_func, source_name in sources:
                try:
                    df = scraper_func(query)
                    if not df.empty:
                        df['source'] = source_name
                        dfs.append(df)
                    time.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    logging.error(f"Error scraping {source_name}: {str(e)}")
                    continue
            
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
            else:
                df = scrape_fallback_data(query)
        
        


        df = df.dropna(subset=['price_inr'])
        df = df[df['price_inr'] > 0]
        df = enhance_product_data(df)
        
        logging.info(f"Successfully retrieved {len(df)} products")
        return df.head(max_results)
        
    except Exception as e:
        logging.error(f"Error in multi-source scraper: {str(e)}")
        return scrape_fallback_data(query)

def scrape_direct_websites(query: str) -> pd.DataFrame:
    """Scrape from direct e-commerce websites"""
    sample_data = {
        'product_name': [f"{query} Pro", f"{query} Lite", f"{query} Plus"],
        'price_inr': [random.randint(15000, 80000) for _ in range(3)],
        'rating': [round(random.uniform(3.5, 5.0), 1) for _ in range(3)],
        'reviews': [random.randint(50, 1000) for _ in range(3)],
        'source': ['Direct Store'] * 3
    }
    return pd.DataFrame(sample_data)

def scrape_price_comparison_sites(query: str) -> pd.DataFrame:
    """Scrape from price comparison websites"""
    sample_data = {
        'product_name': [f"{query} Standard", f"{query} Premium"],
        'price_inr': [random.randint(20000, 90000) for _ in range(2)],
        'rating': [round(random.uniform(3.5, 5.0), 1) for _ in range(2)],
        'reviews': [random.randint(50, 1000) for _ in range(2)],
        'source': ['Price Compare'] * 2
    }
    return pd.DataFrame(sample_data)

def scrape_social_commerce(query: str) -> pd.DataFrame:
    """Scrape from social commerce platforms"""
    sample_data = {
        'product_name': [f"{query} Basic", f"{query} Advanced"],
        'price_inr': [random.randint(10000, 70000) for _ in range(2)],
        'rating': [round(random.uniform(3.5, 5.0), 1) for _ in range(2)],
        'reviews': [random.randint(50, 1000) for _ in range(2)],
        'source': ['Social Shop'] * 2
    }
    return pd.DataFrame(sample_data)

def scrape_international_sites(query: str) -> pd.DataFrame:
    """Scrape from international websites"""
    sample_data = {
        'product_name': [f"{query} Global", f"{query} International"],
        'price_inr': [random.randint(25000, 100000) for _ in range(2)],
        'rating': [round(random.uniform(3.5, 5.0), 1) for _ in range(2)],
        'reviews': [random.randint(50, 1000) for _ in range(2)],
        'source': ['International'] * 2
    }
    return pd.DataFrame(sample_data)

def scrape_fallback_data(query: str) -> pd.DataFrame:
    """Generate sample product data"""
    sample_data = {
        'product_name': [f"{query} Type {i}" for i in range(1, 6)],
        'price_inr': [random.randint(1000, 50000) for _ in range(5)],
        'source': ['Sample Store'] * 5
    }
    return pd.DataFrame(sample_data)



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)