# app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database config using environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'crypto'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'pass123')
}

# Streamlit page setup
st.set_page_config(page_title="Crypto Dashboard", layout="wide")
st.title("🚀 Cryptocurrency Dashboard")

# 1️⃣ Fetch crypto data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin,ethereum,cardano,polkadot,chainlink',
        'vs_currencies': 'usd',
        'include_market_cap': 'true',
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        records = []
        for coin, info in data.items():
            records.append({
                'coin_name': coin,
                'price': float(info['usd']),
                'market_cap': float(info.get('usd_market_cap', 0) or 0),
                'volume': float(info.get('usd_24h_vol', 0) or 0),
                'change_24h': float(info.get('usd_24h_change', 0) or 0),
                'timestamp': datetime.now()
            })
        return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()  # Return empty dataframe on error

data = get_crypto_data()

if not data.empty:
    st.subheader("Latest Crypto Prices")
    st.dataframe(data)
else:
    st.warning("Unable to fetch cryptocurrency data. Please try again later.")

# 2️⃣ Save to database
def save_to_db(df):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO crypto_prices (coin_name, price, market_cap, volume, change_24h, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (row['coin_name'], row['price'], row['market_cap'], row['volume'], row['change_24h'], row['timestamp']))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

if st.button("💾 Save to Database"):
    if not data.empty:
        success = save_to_db(data)
        if success:
            st.success("✅ Data saved to database!")
    else:
        st.warning("No data to save. Please fetch data first.")

# 3️⃣ Charts - Only show if we have data
if not data.empty:
    st.subheader("Crypto Charts")
    
    # Create a tabbed interface for better organization
    tab1, tab2, tab3, tab4 = st.tabs(["Prices", "24h Changes", "Market Caps", "Volume vs Price"])
    
    with tab1:
        st.write("### Current Prices (USD)")
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(data=data, x='coin_name', y='price', ax=ax1)
        ax1.tick_params(axis='x', rotation=45)
        ax1.set_ylabel("Price (USD)")
        st.pyplot(fig1)
    
    with tab2:
        st.write("### 24h Price Changes (%)")
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        colors = ['red' if x < 0 else 'green' for x in data['change_24h']]
        sns.barplot(data=data, x='coin_name', y='change_24h', palette=colors, ax=ax2)
        ax2.tick_params(axis='x', rotation=45)
        ax2.set_ylabel("24h Change (%)")
        st.pyplot(fig2)
    
    with tab3:
        st.write("### Market Capitalization")
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        market_cap_data = data.copy()
        market_cap_data['market_cap_billions'] = market_cap_data['market_cap'] / 1e9
        sns.barplot(data=market_cap_data, x='coin_name', y='market_cap_billions', ax=ax3)
        ax3.tick_params(axis='x', rotation=45)
        ax3.set_ylabel("Market Cap (Billions USD)")
        st.pyplot(fig3)
    
    with tab4:
        st.write("### Volume vs Price")
        fig4, ax4 = plt.subplots(figsize=(10, 6))
        sns.scatterplot(data=data, x='volume', y='price', s=100, ax=ax4)
        
        # Add coin names to scatter plot
        for i, row in data.iterrows():
            ax4.annotate(row['coin_name'], (row['volume'], row['price']))
        
        ax4.set_xlabel("24h Volume (USD)")
        ax4.set_ylabel("Price (USD)")
        st.pyplot(fig4)
else:
    st.info("Charts will appear here once data is available.")

