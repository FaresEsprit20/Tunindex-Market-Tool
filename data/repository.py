# data/repository.py

import psycopg2
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

TABLE_NAME = "stocks"

class MarketRepository:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        self.cur = self.conn.cursor()
        self.create_table()  # ensure table exists on init

    def create_table(self):
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            symbol TEXT PRIMARY KEY,
            company_name TEXT,
            ownership_type TEXT,
            activity_type TEXT,
            price REAL,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            volume REAL,
            market_cap REAL,
            eps REAL,
            book_value_per_share REAL,
            total_equity REAL,
            shares_outstanding REAL,
            pe_ratio REAL,
            roe REAL,
            roa REAL,
            debt_equity REAL,
            profit_margin REAL,
            fair_value REAL,
            margin_of_safety REAL,
            source TEXT
        );
        """
        self.cur.execute(create_sql)
        self.conn.commit()

    def upsert_stock(self, stock):
        upsert_sql = f"""
        INSERT INTO {TABLE_NAME} (symbol, company_name, ownership_type, activity_type, price, open_price,
                                  high_price, low_price, volume, market_cap, eps, book_value_per_share,
                                  total_equity, shares_outstanding, pe_ratio, roe, roa, debt_equity,
                                  profit_margin, fair_value, margin_of_safety, source)
        VALUES (%(symbol)s, %(company_name)s, %(ownership_type)s, %(activity_type)s, %(price)s,
                %(open_price)s, %(high_price)s, %(low_price)s, %(volume)s, %(market_cap)s,
                %(eps)s, %(book_value_per_share)s, %(total_equity)s, %(shares_outstanding)s,
                %(pe_ratio)s, %(roe)s, %(roa)s, %(debt_equity)s, %(profit_margin)s, %(fair_value)s,
                %(margin_of_safety)s, %(source)s)
        ON CONFLICT (symbol) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            ownership_type = EXCLUDED.ownership_type,
            activity_type = EXCLUDED.activity_type,
            price = EXCLUDED.price,
            open_price = EXCLUDED.open_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            volume = EXCLUDED.volume,
            market_cap = EXCLUDED.market_cap,
            eps = EXCLUDED.eps,
            book_value_per_share = EXCLUDED.book_value_per_share,
            total_equity = EXCLUDED.total_equity,
            shares_outstanding = EXCLUDED.shares_outstanding,
            pe_ratio = EXCLUDED.pe_ratio,
            roe = EXCLUDED.roe,
            roa = EXCLUDED.roa,
            debt_equity = EXCLUDED.debt_equity,
            profit_margin = EXCLUDED.profit_margin,
            fair_value = EXCLUDED.fair_value,
            margin_of_safety = EXCLUDED.margin_of_safety,
            source = EXCLUDED.source;
        """
        self.cur.execute(upsert_sql, stock)
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()