import streamlit as st
import pandas as pd
import plotly.express as px
from data.scrapers.scraper_utils import scrape_multiple_sources
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def get_gemini_api_key():
    """Get Gemini API key from environment or Streamlit secrets"""
    
    api_key = os.getenv("GEMINI_API_KEY")
 

    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (KeyError, AttributeError):
            pass
    
    return api_key

GEMINI_API_KEY = get_gemini_api_key()
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

def get_ollama_response(model_name: str, prompt: str, context: str = "") -> str:
    full_prompt = f"{context}\n\nUser: {prompt}"
    try:
        payload = {
            "model": model_name,
            "prompt": full_prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "No response field in JSON")
    except requests.exceptions.ConnectionError:
        return "Oh no! (╯°□°）╯︵ ┻━┻ It seems I can't connect to the local Ollama models. Make sure Ollama is running! For now, you can use my online friend, the Gemini Buddy! ✨"
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
    except requests.exceptions.JSONDecodeError:
        return "Error: Could not decode JSON response from Ollama."

def get_gemini_response(prompt: str, history: list):
    if not GEMINI_API_KEY:
        return "Gemini API key not configured. Please set it in the .env file. (｡•̀ᴗ•́｡)"
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred with Gemini: {e}"

def search_products(query: str) -> tuple:
    df = scrape_multiple_sources(query)
    os.makedirs("exports", exist_ok=True)
    csv_path = f"exports/{query}_products.csv"
    df.to_csv(csv_path, index=False)
    
    if df.empty:
        return None, "No products found on the specified websites.", df
        
    currency_display_symbol = df['currency_symbol'].iloc[0] if not df.empty else "₹"

    fig = px.bar(df, x='product_name', y='price_value', color='source', title=f"☆ Price Comparison ({currency_display_symbol}) ☆", template="plotly_dark")
    
    stats = f"""
    - **(｡◕‿◕｡) Products Found:** {len(df)}
    - **(｡◕‿◕｡) Average Price:** {currency_display_symbol}{df['price_value'].mean():,.2f}
    - **(｡◕‿◕｡) Lowest Price:** {currency_display_symbol}{df['price_value'].min():,.2f}
    - **(｡◕‿◕｡) CSV saved to:** `{csv_path}`
    """
    return fig, stats, df

def load_css():
    st.markdown("""
    <style>
    .stApp { background-color: #1E1E1E; color: #FAFAFA; }
    .stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { background-color: #2E2E2E; }
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(layout="wide", page_title="DataWeaver", page_icon="✨")
load_css()

st.sidebar.title("Menu")
page = st.sidebar.radio("Select", ["Product Analysis", "Chat with Data (Ollama)", "Gemini Buddy"])

if "gemini_messages" not in st.session_state:
    st.session_state.gemini_messages = []
if "data_chat_messages" not in st.session_state:
    st.session_state.data_chat_messages = []
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = None
if "ollama_model" not in st.session_state:
    st.session_state.ollama_model = "qwen2.5-coder:7b" 

if page == "Product Analysis":
    st.title("✨ DataWeaver ✨")
    st.header("Product Price Analysis (｡◕‿◕｡)")
    query_input = st.text_input("Search for a product:", placeholder="Enter product name...")
    if st.button("Search ＼(^o^)／"):
        if query_input:
            with st.spinner("Weaving data... (～￣▽￣)～"):
                fig, stats, df = search_products(query_input)
                st.session_state.scraped_data = df
                st.session_state.data_chat_messages = [] 
                st.session_state.gemini_messages = []
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Statistics ☆")
                        st.markdown(stats)
                    with col2:
                        st.subheader("Raw Data ☆")
                        st.dataframe(df)
                    st.success("Data woven! Navigate to the chat pages to ask questions. ＼(^o^)／")
                else:
                    st.warning(stats)
        else:
            st.warning("Please enter a product name to search. (´･ω･`)")

elif page == "Chat with Data (Ollama)":
    st.title("Chat with Your Data (｡◕‿◕｡)")
    
    ollama_model_input = st.text_input(
        "Enter Ollama Model Name:",
        value=st.session_state.ollama_model,
        placeholder="e.g., qwen2.5-coder:7b"
    )
    st.session_state.ollama_model = ollama_model_input 

    if st.session_state.scraped_data is not None:
        for msg in st.session_state.data_chat_messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Ask about the data..."):
            st.session_state.data_chat_messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.spinner("Ollama is analyzing... (ง •̀_•́)ง"):
                df_markdown = st.session_state.scraped_data.to_markdown()
                data_context = f"Here is the data you are analyzing:\n\n{df_markdown}\n\nNow, please answer the user's question based on this data."
                
                response = get_ollama_response(st.session_state.ollama_model, prompt, context=data_context)
                st.session_state.data_chat_messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
    else:
        st.warning("Please weave some data first on the 'Product Analysis' page. ＼(^o^)／")

elif page == "Gemini Buddy":
    st.title("Your Gemini Buddy (｡◕‿◕｡)")
    for msg in st.session_state.gemini_messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Send a message..."):
        st.session_state.gemini_messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.spinner("Gemini is thinking... ( ´ ω ` )"):
            gemini_history = []
            context_added = False
            if st.session_state.scraped_data is not None:
                df_markdown = st.session_state.scraped_data.to_markdown()
                context = f"CONTEXT: Here is some data the user just scraped. Use it to answer their questions.\n\n{df_markdown}"
                gemini_history.append({"role": "user", "parts": [context]})
                gemini_history.append({"role": "model", "parts": ["Got it! I have the data. What would you like to know? (｡◕‿◕｡)"]})
                context_added = True

            for msg in st.session_state.gemini_messages:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})
            
            response = get_gemini_response(prompt, gemini_history)
            st.session_state.gemini_messages.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)
