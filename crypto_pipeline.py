import requests
import pandas as pd
import psycopg2
import seaborn as sns
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession
from datetime import datetime
import warnings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

warnings.filterwarnings('ignore')

class SimpleCryptoPipeline:
    def __init__(self):
        # Database connection using environment variables
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'crypto'),
            'user': os.getenv('DB_USER', 'user'),
            'password': os.getenv('DB_PASSWORD', 'pass123')
        }
        
        # Initialize Spark
        self.spark = SparkSession.builder \
            .appName("CryptoPipeline") \
            .getOrCreate()
        
        print("✅ Pipeline initialized!")
    
    def get_crypto_data(self):
        """Get crypto data from free API"""
        print("📡 Getting crypto data...")
        
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum,cardano,polkadot,chainlink',
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true'
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            print(f"✅ Got data for {len(data)} coins")
            return data
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def process_with_spark(self, data):
        """Process data using Spark"""
        print("⚡ Processing with Spark...")
        
        # Convert to list of dictionaries for Spark with consistent data types
        records = []
        for coin, info in data.items():
            records.append({
                'coin_name': str(coin),
                'price': float(info['usd']),
                'market_cap': float(info.get('usd_market_cap', 0) or 0),
                'volume': float(info.get('usd_24h_vol', 0) or 0),
                'change_24h': float(info.get('usd_24h_change', 0) or 0),
                'timestamp': datetime.now()
            })
        
        # Create Spark DataFrame
        df = self.spark.createDataFrame(records)
        
        # Simple processing: filter coins with price > $1
        processed_df = df.filter(df.price > 1.0)
        
        print(f"✅ Processed {processed_df.count()} records")
        return processed_df.toPandas()  # Convert back to Pandas
    
    def save_to_database(self, df):
        """Save data to PostgreSQL"""
        print("💾 Saving to database...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Insert each row
            for _, row in df.iterrows():
                cur.execute("""
                    INSERT INTO crypto_prices (coin_name, price, market_cap, volume, change_24h, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (row['coin_name'], row['price'], row['market_cap'], 
                     row['volume'], row['change_24h'], row['timestamp']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"✅ Saved {len(df)} records to database")
            return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def create_charts(self):
        """Create charts with Seaborn"""
        print("📊 Creating charts...")
        
        try:
            # Get data from database
            conn = psycopg2.connect(**self.db_config)
            df = pd.read_sql("SELECT * FROM crypto_prices ORDER BY timestamp DESC LIMIT 50", conn)
            conn.close()
            
            if len(df) == 0:
                print("❌ No data to chart")
                return
            
            # Set up the plotting style
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Create subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Cryptocurrency Dashboard', fontsize=16, fontweight='bold')
            
            # Chart 1: Price comparison
            latest_data = df.groupby('coin_name')['price'].last().reset_index()
            sns.barplot(data=latest_data, x='coin_name', y='price', ax=axes[0,0])
            axes[0,0].set_title('Current Prices (USD)')
            axes[0,0].tick_params(axis='x', rotation=45)
            
            # Chart 2: 24h Change
            change_data = df.groupby('coin_name')['change_24h'].last().reset_index()
            colors = ['red' if x < 0 else 'green' for x in change_data['change_24h']]
            sns.barplot(data=change_data, x='coin_name', y='change_24h', palette=colors, ax=axes[0,1])
            axes[0,1].set_title('24h Price Change (%)')
            axes[0,1].tick_params(axis='x', rotation=45)
            
            # Chart 3: Market Cap
            mcap_data = df.groupby('coin_name')['market_cap'].last().reset_index()
            mcap_data['market_cap_billions'] = mcap_data['market_cap'] / 1e9
            sns.barplot(data=mcap_data, x='coin_name', y='market_cap_billions', ax=axes[1,0])
            axes[1,0].set_title('Market Cap (Billions USD)')
            axes[1,0].tick_params(axis='x', rotation=45)
            
            # Chart 4: Volume vs Price scatter
            volume_data = df.groupby('coin_name').agg({'volume': 'last', 'price': 'last'}).reset_index()
            sns.scatterplot(data=volume_data, x='volume', y='price', s=100, ax=axes[1,1])
            axes[1,1].set_title('Volume vs Price')
            axes[1,1].set_xlabel('24h Volume (USD)')
            axes[1,1].set_ylabel('Price (USD)')
            
            # Add coin names to scatter plot
            for i, row in volume_data.iterrows():
                axes[1,1].annotate(row['coin_name'], (row['volume'], row['price']))
            
            plt.tight_layout()
            plt.savefig('crypto_dashboard.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            print("✅ Charts created and saved as 'crypto_dashboard.png'")
            
        except Exception as e:
            print(f"❌ Chart error: {e}")
    
    def run_full_pipeline(self):
        """Run the complete pipeline"""
        print("🚀 Starting Crypto Pipeline!")
        print("=" * 50)
        
        # Step 1: Extract data
        data = self.get_crypto_data()
        if not data:
            return False
        
        # Step 2: Process with Spark
        processed_df = self.process_with_spark(data)
        
        # Step 3: Load to database
        success = self.save_to_database(processed_df)
        if not success:
            return False
        
        # Step 4: Create visualizations
        self.create_charts()
        
        print("=" * 50)
        print("🎉 Pipeline completed successfully!")
        return True

# Run the pipeline
if __name__ == "__main__":
    pipeline = SimpleCryptoPipeline()
    pipeline.run_full_pipeline()