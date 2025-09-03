# 🚀 Cryptocurrency Data Pipeline & Dashboard

A comprehensive data engineering project that extracts, processes, and visualizes cryptocurrency data using modern tools including Apache Spark, PostgreSQL, and Streamlit.

## 🏗️ Architecture Overview

```
CoinGecko API → Apache Spark → PostgreSQL → Streamlit Dashboard
                    ↓
                Seaborn/Matplotlib Charts
```

## ✨ Features

- **Real-time Data Extraction**: Fetches live cryptocurrency data from CoinGecko API
- **Big Data Processing**: Uses Apache Spark for scalable data processing
- **Database Storage**: PostgreSQL for reliable data persistence
- **Interactive Dashboard**: Streamlit web interface with real-time updates
- **Data Visualization**: Beautiful charts using Seaborn and Matplotlib
- **Containerized Deployment**: Docker Compose for easy deployment
- **Error Handling**: Robust error handling and data validation

## 🛠️ Technology Stack

- **Backend**: Python 3.9
- **Data Processing**: Apache Spark (PySpark)
- **Database**: PostgreSQL 15
- **Web Framework**: Streamlit
- **Visualization**: Seaborn, Matplotlib
- **Containerization**: Docker & Docker Compose
- **Database Admin**: pgAdmin4
- **Environment Management**: python-dotenv

## 📊 Data Pipeline Components

### 1. Data Extraction
- Connects to CoinGecko API (free tier)
- Extracts data for Bitcoin, Ethereum, Cardano, Polkadot, and Chainlink
- Includes price, market cap, volume, and 24h change data

### 2. Data Processing (Apache Spark)
- Processes data using Spark DataFrames
- Performs data validation and filtering
- Handles data type conversions and null values
- Scalable for processing larger datasets

### 3. Data Storage
- PostgreSQL database with optimized schema
- Automatic table creation via init.sql
- ACID compliance for data integrity
- Indexed for query performance

### 4. Data Visualization
- Real-time Streamlit dashboard
- Interactive charts and tables
- Price trends and market analysis
- Volume vs. price correlations

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git for version control

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd crypto-data-pipeline
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations (defaults work for local development)
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the applications**
   - **Streamlit Dashboard**: http://localhost:8501
   - **pgAdmin**: http://localhost:8080
     - Email: admin@admin.com
     - Password: admin123

## 📈 Dashboard Features

### Main Dashboard (Streamlit)
- **Live Data Table**: Current prices and market data
- **Price Charts**: Bar charts showing current cryptocurrency prices
- **24h Change Analysis**: Color-coded gains/losses visualization
- **Market Cap Comparison**: Market capitalization in billions
- **Volume vs Price Scatter Plot**: Trading volume analysis

### Data Pipeline (Command Line)
```bash
# Run the full ETL pipeline
python crypto_pipeline.py
```

## 🗄️ Database Schema

```sql
CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    coin_name VARCHAR(50),
    price DECIMAL(15,2),
    market_cap BIGINT,
    volume BIGINT,
    change_24h DECIMAL(10,4),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Database Configuration
DB_HOST=crypto_db
DB_PORT=5432
DB_NAME=crypto
DB_USER=user
DB_PASSWORD=your_secure_password
```

### Supported Cryptocurrencies
- Bitcoin (BTC)
- Ethereum (ETH)
- Cardano (ADA)
- Polkadot (DOT)
- Chainlink (LINK)

## 📱 Usage Examples

### Streamlit Dashboard
1. Open http://localhost:8501
2. View real-time cryptocurrency data
3. Click "Save to Database" to persist current data
4. Explore different chart tabs for various analyses

### Manual Pipeline Execution
```bash
# Run inside the container or with proper Python environment
python crypto_pipeline.py
```

## 🧪 Development Setup

### Local Development (without Docker)

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL locally**
   ```bash
   # Install PostgreSQL and create database
   createdb crypto
   psql crypto < init.sql
   ```

3. **Configure environment**
   ```bash
   export DB_HOST=localhost
   export DB_USER=your_user
   # ... other variables
   ```

4. **Run applications**
   ```bash
   # Start Streamlit dashboard
   streamlit run app.py

   # Run ETL pipeline
   python crypto_pipeline.py
   ```

## 📊 Monitoring & Observability

### Health Checks
- PostgreSQL health check in docker-compose
- API response validation
- Database connection testing

### Logging
- Comprehensive error logging
- Pipeline execution status
- Data quality validation logs

## 🔒 Security Features

- Environment variable management
- Database connection pooling
- Input validation and sanitization
- Docker container isolation

## 🚀 Scaling Considerations

### Horizontal Scaling
- Spark can be configured for cluster mode
- PostgreSQL can be set up with read replicas
- Multiple Streamlit instances behind load balancer

### Performance Optimization
- Database indexing on timestamp and coin_name
- Spark DataFrame caching for repeated operations
- Streamlit data caching (5-minute TTL)

## 📋 Project Structure

```
crypto-data-pipeline/
├── app.py                 # Streamlit dashboard application
├── crypto_pipeline.py     # Main ETL pipeline with Spark
├── docker-compose.yml     # Docker services configuration
├── Dockerfile            # Application container setup
├── init.sql              # Database initialization
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
├── .dockerignore        # Docker ignore rules
└── README.md            # Project documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- CoinGecko for providing free cryptocurrency API
- Apache Spark community for the excellent big data processing framework
- Streamlit team for the intuitive web framework

## 📞 Contact

Your Name - your.email@example.com
Project Link: [https://github.com/yourusername/crypto-data-pipeline](https://github.com/yourusername/crypto-data-pipeline)

---

⭐ **Star this repository if you found it helpful!**