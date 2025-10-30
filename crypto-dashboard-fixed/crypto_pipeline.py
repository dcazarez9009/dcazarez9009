import requests
import pandas as pd
import psycopg2
from psycopg2 import pool as psycopg2_pool
import seaborn as sns
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from datetime import datetime
import warnings
import os
import atexit
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

warnings.filterwarnings('ignore')

class SimpleCryptoPipeline:
    _spark_instance = None
    _conn_pool = None
    
    def __init__(self):
        # Database connection using environment variables
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'crypto'),
            'user': os.getenv('DB_USER', 'user'),
            'password': os.getenv('DB_PASSWORD', 'pass123')
        }
        
        # Initialize connection pool once
        if SimpleCryptoPipeline._conn_pool is None:
            SimpleCryptoPipeline._conn_pool = psycopg2_pool.SimpleConnectionPool(
                1, 10,  # min=1, max=10 connections
                **self.db_config
            )
        
        # Reuse Spark session instead of creating new one
        self.spark = self._get_or_create_spark_session()
        
        print("✅ Pipeline initialized!")
    
    @classmethod
    def _get_or_create_spark_session(cls):
        """Singleton Spark session to avoid recreation overhead"""
        if cls._spark_instance is None or cls._spark_instance._jsc.sc().isStopped():
            cls._spark_instance = SparkSession.builder \
                .appName("CryptoPipeline") \
                .master("local[4]") \
                .config("spark.executor.memory", "2g") \
                .config("spark.driver.memory", "2g") \
                .config("spark.sql.shuffle.partitions", "8") \
                .config("spark.default.parallelism", "8") \
                .config("spark.rdd.compress", "true") \
                .config("spark.shuffle.compress", "true") \
                .getOrCreate()
        
        return cls._spark_instance
    
    def get_crypto_data(self):
        """Get crypto data from free API"""
        print("📡 Getting crypto data...")
        
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
            response.raise_for_status()
            data = response.json()
            print(f"✅ Got data for {len(data)} coins")
            return data
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def process_with_spark(self, data):
        """Process data using Spark with optimized schema"""
        print("⚡ Processing with Spark...")
        
        # Convert to list efficiently
        records = []
        fetched_at = datetime.utcnow()
        for item in data:
            last_updated = item.get('last_updated')
            price_ts = None
            if last_updated:
                try:
                    price_ts = pd.to_datetime(last_updated, utc=True).to_pydatetime()
                except Exception:
                    price_ts = None
            records.append({
                'coin_name': str(item.get('id')),
                'price': float(item.get('current_price') or 0),
                'market_cap': float(item.get('market_cap') or 0),
                'volume': float(item.get('total_volume') or 0),
                'change_24h': float(item.get('price_change_percentage_24h') or 0),
                'timestamp': fetched_at,       # backward-compat
                'fetched_at': fetched_at,
                'price_timestamp': price_ts
            })
        
        # Create DataFrame with explicit schema (faster than inference)
        schema = StructType([
            StructField("coin_name", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("market_cap", DoubleType(), True),
            StructField("volume", DoubleType(), True),
            StructField("change_24h", DoubleType(), True),
            StructField("timestamp", TimestampType(), True),
            StructField("fetched_at", TimestampType(), True),
            StructField("price_timestamp", TimestampType(), True),
        ])
        
        df = self.spark.createDataFrame(records, schema=schema)
        
        # Push-down predicate filtering (more efficient)
        processed_df = df.filter(df.price > 1.0)
        
        # Cache to avoid recomputation
        processed_df.cache()
        count = processed_df.count()
        
        print(f"✅ Processed {count} records")
        return processed_df.toPandas()
    
    def save_to_database(self, df):
        """Save data using pooled connection with batch insert"""
        print("💾 Saving to database...")
        
        try:
            conn = SimpleCryptoPipeline._conn_pool.getconn()
            cur = conn.cursor()
            
            # Convert DataFrame to tuples for batch insert
            records = [(
                row['coin_name'], row['price'], row['market_cap'], row['volume'], row['change_24h'],
                row['timestamp'], row.get('fetched_at'), row.get('price_timestamp')
            ) for _, row in df.iterrows()]
            
            # Batch insert
            cur.executemany("""
                INSERT INTO crypto_prices (
                    coin_name, price, market_cap, volume, change_24h,
                    timestamp, fetched_at, price_timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, records)
            
            conn.commit()
            cur.close()
            SimpleCryptoPipeline._conn_pool.putconn(conn)
            
            print(f"✅ Saved {len(df)} records to database (batch insert)")
            return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def create_charts(self):
        """Create charts with Seaborn"""
        print("📊 Creating charts...")
        
        try:
            # Get data from database
            conn = SimpleCryptoPipeline._conn_pool.getconn()
            df = pd.read_sql("SELECT * FROM crypto_prices ORDER BY timestamp DESC LIMIT 50", conn)
            SimpleCryptoPipeline._conn_pool.putconn(conn)
            
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
            plt.close()
            
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

# Register cleanup at exit
def cleanup_spark():
    if SimpleCryptoPipeline._spark_instance is not None:
        SimpleCryptoPipeline._spark_instance.stop()

atexit.register(cleanup_spark)

# Run the pipeline
if __name__ == "__main__":
    pipeline = SimpleCryptoPipeline()
    pipeline.run_full_pipeline()