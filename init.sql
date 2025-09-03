CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    coin_name VARCHAR(50),
    price DECIMAL(15,2),
    market_cap BIGINT,
    volume BIGINT,
    change_24h DECIMAL(10,4),
    timestamp TIMESTAMP DEFAULT NOW()
);

INSERT INTO crypto_prices (coin_name, price, market_cap, volume, change_24h) VALUES
('Bitcoin', 43000.00, 840000000000, 25000000000, 2.5),
('Ethereum', 2600.00, 312000000000, 12000000000, -1.2);