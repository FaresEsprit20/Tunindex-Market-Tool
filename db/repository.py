# data/repository.py

from psycopg2.extras import RealDictCursor
from data.connection import get_connection


class MarketRepository:
    def __init__(self):
        self.conn = get_connection()
        self.conn.autocommit = True

    # -------------------------
    # UPSERT
    # -------------------------
    def upsert_stock(self, stock: dict):
        query = """
        INSERT INTO stocks (
            symbol, company_name,
            ownership_type, activity_type,
            price, open_price, high_price, low_price,
            volume, market_cap,
            eps, book_value_per_share, total_equity, shares_outstanding,
            pe_ratio, roe, roa, debt_equity, profit_margin,
            fair_value, margin_of_safety,
            source, last_updated
        )
        VALUES (
            %(symbol)s, %(company_name)s,
            %(ownership_type)s, %(activity_type)s,
            %(price)s, %(open_price)s, %(high_price)s, %(low_price)s,
            %(volume)s, %(market_cap)s,
            %(eps)s, %(book_value_per_share)s, %(total_equity)s, %(shares_outstanding)s,
            %(pe_ratio)s, %(roe)s, %(roa)s, %(debt_equity)s, %(profit_margin)s,
            %(fair_value)s, %(margin_of_safety)s,
            %(source)s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (symbol)
        DO UPDATE SET
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

            source = EXCLUDED.source,
            last_updated = CURRENT_TIMESTAMP;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, stock)

    # -------------------------
    # FETCH ALL
    # -------------------------
    def fetch_all(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM stocks ORDER BY symbol;")
            return cur.fetchall()

    # -------------------------
    # FETCH ONE
    # -------------------------
    def fetch_one(self, symbol):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM stocks WHERE symbol=%s;", (symbol,))
            return cur.fetchone()

    # -------------------------
    # TOP STOCKS (MOS)
    # -------------------------
    def fetch_top(self, limit=10):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM stocks
                WHERE margin_of_safety IS NOT NULL
                ORDER BY margin_of_safety DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

    # -------------------------
    # UNDERVALUED
    # -------------------------
    def fetch_undervalued(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM stocks
                WHERE fair_value IS NOT NULL
                  AND price IS NOT NULL
                  AND fair_value > price
                ORDER BY (fair_value - price) DESC;
            """)
            return cur.fetchall()

    # -------------------------
    # CLOSE
    # -------------------------
    def close(self):
        if self.conn:
            self.conn.close()