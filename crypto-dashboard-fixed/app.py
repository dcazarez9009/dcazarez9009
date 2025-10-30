# app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    # Use markets endpoint to get per-coin last_updated (market timestamp)
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'ids': 'bitcoin,ethereum,cardano,polkadot,chainlink',
        'price_change_percentage': '24h',
        'order': 'market_cap_desc',
        'per_page': 250,
        'page': 1,
        'sparkline': 'false'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        fetched_at = datetime.utcnow()
        records = []
        for item in data:
            # CoinGecko returns ISO 8601 e.g. "2024-01-01T12:34:56.789Z"
            last_updated = item.get('last_updated')
            price_ts = None
            if last_updated:
                try:
                    price_ts = pd.to_datetime(last_updated, utc=True).to_pydatetime()
                except Exception:
                    price_ts = None
            records.append({
                'coin_name': item.get('id'),
                'price': float(item.get('current_price') or 0),
                'market_cap': float(item.get('market_cap') or 0),
                'volume': float(item.get('total_volume') or 0),
                'change_24h': float(item.get('price_change_percentage_24h') or 0),
                'timestamp': fetched_at,          # backward-compat: same as fetched_at
                'fetched_at': fetched_at,
                'price_timestamp': price_ts
            })
        return pd.DataFrame(records)
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()  # Return empty dataframe on error

data = get_crypto_data()

if not data.empty:
    st.subheader("Latest Crypto Prices")
    # Prepare display with clearer timestamps
    df_display = data.copy()
    if 'timestamp' in df_display.columns:
        df_display = df_display.rename(columns={'timestamp': 'legacy_timestamp'})
    # Arrange columns to highlight fetched_at and price_timestamp
    preferred_cols = [
        'coin_name', 'price', 'market_cap', 'volume', 'change_24h',
        'fetched_at', 'price_timestamp'
    ]
    # Include legacy_timestamp only if user opts in
    show_legacy = st.checkbox("Show legacy timestamp column", value=False)
    remaining_cols = [c for c in df_display.columns if c not in preferred_cols]
    ordered_cols = [c for c in preferred_cols if c in df_display.columns] + remaining_cols
    if not show_legacy and 'legacy_timestamp' in ordered_cols:
        ordered_cols = [c for c in ordered_cols if c != 'legacy_timestamp']
    df_display = df_display[ordered_cols]
    st.dataframe(df_display, use_container_width=True)
    st.caption("fetched_at = when your app saved the data; price_timestamp = market's last_updated; legacy_timestamp kept for backward compatibility.")
else:
    st.warning("Unable to fetch cryptocurrency data. Please try again later.")

# 2️⃣ Save to database
def save_to_db(df):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO crypto_prices (
                    coin_name, price, market_cap, volume, change_24h,
                    timestamp, fetched_at, price_timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['coin_name'], row['price'], row['market_cap'], row['volume'], row['change_24h'],
                row.get('timestamp'), row.get('fetched_at'), row.get('price_timestamp')
            ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Saved {len(df)} records to database")
        return True
    except Exception as e:
        logger.error(f"Database error: {e}")
        st.error(f"Database error: {e}")
        return False

col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Save to Database"):
        if not data.empty:
            success = save_to_db(data)
            if success:
                st.success("✅ Data saved to database!")
        else:
            st.warning("No data to save. Please fetch data first.")
    
with col2:
    if st.button("📥 Download CSV for Power BI"):
        if not data.empty:
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Download Latest Data",
                data=csv,
                file_name=f'crypto_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv'
            )

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

