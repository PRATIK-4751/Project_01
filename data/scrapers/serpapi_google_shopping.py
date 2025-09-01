import os
import pandas as pd
from serpapi.google_search import GoogleSearch
from dotenv import load_dotenv
import re
import random
import streamlit as st

# Load environment variables

load_dotenv()

def get_api_key():
    """Get API key from environment or Streamlit secrets"""
  
    api_key = os.getenv("SERPAPI_API_KEY")
    
   


    if not api_key:
        try:
            api_key = st.secrets["SERPAPI_API_KEY"]
        except (KeyError, AttributeError):
            pass
    
    return api_key

def extract_price_and_currency(price_str: str) -> tuple[float, str]:
    """Extracts price and currency symbol from a price string."""
    if price_str is None:
        return 0.0, "₹" # Default to INR symbol

    price_str = str(price_str).strip()
    currency_symbol = "₹" # Default to INR

    # Detect common currency symbols
    if "₹" in price_str:
        currency_symbol = "₹"
    elif "$" in price_str:
        currency_symbol = "$"
    elif "€" in price_str:
        currency_symbol = "€"
    elif "£" in price_str:
        currency_symbol = "£"
    # Add more currency symbols as needed

    try:
        # Remove currency symbols and commas for cleaning
        cleaned = re.sub(r'[^\d.]', '', price_str)
        if not cleaned:
            return 0.0, currency_symbol
        return float(cleaned), currency_symbol
    except ValueError:
        return 0.0, currency_symbol
    except Exception as e:
        print(f"Unexpected error in extract_price_and_currency: {e}")
        return 0.0, currency_symbol

def generate_fallback_data(query: str, max_results: int = 20) -> pd.DataFrame:
    """Generate sample data when API fails"""
    products = [
        f"{query} Pro Model",
        f"{query} Standard Edition",
        f"{query} Premium Series",
        f"{query} Basic Version",
        f"{query} Advanced Model",
        f"{query} Lite Edition",
        f"{query} Professional",
        f"{query} Ultimate",
        f"{query} Entry Level",
        f"{query} Flagship"
    ]
    
    data = []
    for i in range(min(max_results, len(products))):
        data.append({
            "product_name": products[i],
            "price_inr": random.randint(5000, 80000),
            "source": random.choice(["Amazon", "Flipkart", "Myntra", "Snapdeal"]),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "reviews": random.randint(50, 2000)
        })
    
    return pd.DataFrame(data)

def search_google_shopping(query="laptop", max_results=20):
    """Enhanced Google Shopping search with error handling and data validation"""
    try:
        api_key = get_api_key()
        if not api_key:
            print("SERPAPI_API_KEY not found - using fallback data")
            return generate_fallback_data(query, max_results)

        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": api_key,
            "num": max_results
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        
        shopping_results = results.get("shopping_results", [])
        
        if not shopping_results:
            print("No shopping results found - using fallback data")
            return generate_fallback_data(query, max_results)
        
        processed_results = []
        for item in shopping_results:
            original_price = item.get("price")
            
            # Extract price and currency
            price_value, currency_sym = extract_price_and_currency(original_price or "0")

            # Price plausibility check (example thresholds, adjust as needed)
            if not (10 <= price_value <= 1000000): # Assuming prices between 10 and 1,000,000 units
                print(f"Warning: Price {price_value} for {item.get('title')} seems implausible. Skipping or adjusting.")
                price_value = 0.0 # Mark as invalid or handle differently

            rating_val = item.get("rating")
            if rating_val is None:
                rating = random.uniform(3.5, 5.0)
            else:
                try:
                    rating = float(rating_val)
                    # Rating validation: ensure between 0 and 5
                    if not (0 <= rating <= 5):
                        print(f"Warning: Rating {rating} for {item.get('title')} is out of range. Adjusting to average.")
                        rating = random.uniform(3.5, 5.0)
                except (ValueError, TypeError):
                    rating = random.uniform(3.5, 5.0)
            
            reviews_val = item.get("reviews")
            if reviews_val is None:
                reviews = random.randint(50, 1000)
            else:
                try:
                    reviews = int(reviews_val)
                except (ValueError, TypeError):
                    reviews = random.randint(50, 1000)

            processed_results.append({
                "product_name": item.get("title", "Unknown"),
                "price_value": price_value, # Store the numeric price
                "currency_symbol": currency_sym, # Store the detected currency symbol
                "source": item.get("source", "Google Shopping"),
                "rating": rating,
                "reviews": reviews
            })
        
        df = pd.DataFrame(processed_results)
        return df[df['price_value'] > 0]  # Filter out items with implausible or zero prices
        
    except Exception as e:
        print(f"Error in Google Shopping search: {str(e)}")
        return generate_fallback_data(query, max_results)
