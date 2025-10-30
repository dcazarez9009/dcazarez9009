CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    coin_name VARCHAR(50),
    price DECIMAL(15,2),
    market_cap BIGINT,
    volume BIGINT,
    change_24h DECIMAL(10,4),
    timestamp TIMESTAMP DEFAULT NOW(), -- retained for backward-compat (acts as fetched_at)
    fetched_at TIMESTAMP DEFAULT NOW(),
    price_timestamp TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX idx_coin_name ON crypto_prices(coin_name);
CREATE INDEX idx_timestamp ON crypto_prices(timestamp DESC);
CREATE INDEX idx_coin_timestamp ON crypto_prices(coin_name, timestamp DESC);
CREATE INDEX idx_price_timestamp ON crypto_prices(price_timestamp DESC);

-- Insert sample data
INSERT INTO crypto_prices (coin_name, price, market_cap, volume, change_24h) VALUES
('bitcoin', 43000.00, 840000000000, 25000000000, 2.5),
('ethereum', 2600.00, 312000000000, 12000000000, -1.2),
('cardano', 0.98, 35000000000, 500000000, 0.5),
('polkadot', 8.50, 12000000000, 250000000, 1.2),
('chainlink', 28.50, 14000000000, 450000000, -0.8);