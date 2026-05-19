import sqlite3
import json
import os
from datetime import datetime, timezone

def utc_now_iso_z():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def populate_dummy_data():
    # Try to find the database path from .env or use the standard one
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    db_path = None
    env_path = os.path.join(base_dir, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('DB_PATH='):
                    db_path = line.split('=')[1].strip()
                    if not os.path.isabs(db_path):
                        # DB_PATH in .env is usually relative to service/server if run from there
                        # but let's check both
                        alt_path = os.path.join(base_dir, 'service', 'server', db_path)
                        if os.path.exists(os.path.dirname(alt_path)):
                            db_path = alt_path
                        else:
                            db_path = os.path.join(base_dir, db_path)
                    break
    
    if not db_path:
        db_path = os.path.join(base_dir, 'service', 'server', 'data', 'clawtrader.db')
    
    print(f"Connecting to database at: {db_path}")
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    created_at = utc_now_iso_z()

    # Ensure we have at least one agent
    print("Checking for agents...")
    cursor.execute("SELECT id FROM agents LIMIT 1")
    agent_row = cursor.fetchone()
    if not agent_row:
        print("Inserting dummy agent '托马斯'...")
        cursor.execute(
            "INSERT INTO agents (name, token, cash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ("托马斯", "dummy-token-1", 100000.0, created_at, created_at)
        )
        agent_id = cursor.lastrowid
    else:
        agent_id = agent_row['id']

    print("Inserting dummy signals...")
    # Add some signals for different markets
    markets_to_populate = ["us-stock", "crypto", "polymarket"]
    symbols = {
        "us-stock": ["NVDA", "AAPL", "TSLA"],
        "crypto": ["BTC", "ETH", "SOL"],
        "polymarket": ["FED-CUT-JUNE", "TRUMP-WIN-2026"]
    }
    
    # Get current max signal_id
    cursor.execute("SELECT COALESCE(MAX(signal_id), 0) FROM signals")
    max_id = cursor.fetchone()[0]

    for market in markets_to_populate:
        for i, symbol in enumerate(symbols[market]):
            max_id += 1
            side = "buy" if i % 2 == 0 else "short"
            price = 100.0 + i * 10
            cursor.execute(
                """
                INSERT INTO signals 
                (signal_id, agent_id, message_type, market, signal_type, symbol, side, entry_price, quantity, content, timestamp, created_at, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    max_id, agent_id, "operation", market, "realtime", symbol, side, price, 0.1,
                    f"Test signal for {symbol} in {market}", int(datetime.now().timestamp()), created_at, created_at
                )
            )

    print("Inserting dummy market news...")
    news_items = [
        {
            "title": "Fed Signals Potential Rate Cut in Late 2026",
            "url": "https://example.com/fed-news",
            "source": "MarketWatch",
            "summary": "The Federal Reserve indicated that inflation is cooling faster than expected.",
            "time_published": created_at,
            "overall_sentiment_label": "Bullish",
            "ticker_sentiment": [{"ticker": "SPY", "sentiment_label": "Bullish"}]
        },
        {
            "title": "Tech Earnings Surpass Expectations Across the Board",
            "url": "https://example.com/tech-earnings",
            "source": "Bloomberg",
            "summary": "Major tech companies reported record-breaking revenue growth this quarter.",
            "time_published": created_at,
            "overall_sentiment_label": "Bullish",
            "ticker_sentiment": [{"ticker": "QQQ", "sentiment_label": "Bullish"}]
        }
    ]
    categories = ["equities", "macro", "crypto", "commodities"]
    for cat in categories:
        summary = {
            "category": cat,
            "item_count": len(news_items),
            "activity_level": "active",
            "top_headline": news_items[0]["title"],
            "top_source": "Bloomberg",
            "latest_item_time": created_at
        }
        cursor.execute(
            "INSERT INTO market_news_snapshots (category, snapshot_key, items_json, summary_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (cat, f"{cat}:{created_at}", json.dumps(news_items), json.dumps(summary), created_at)
        )

    print("Inserting dummy macro signals...")
    signals = [
        {"id": "btc_trend", "label": "BTC trend", "status": "bullish", "value": 5.2, "unit": "%", "explanation": "BTC is trending higher."},
        {"id": "qqq_trend", "label": "QQQ trend", "status": "bullish", "value": 3.1, "unit": "%", "explanation": "Tech stocks are strong."},
        {"id": "safe_haven_pressure", "label": "Safe-haven pressure", "status": "neutral", "value": 0.5, "unit": "%", "explanation": "Gold is stable."}
    ]
    meta = {
        "summary": "Risk appetite is leading across the current macro snapshot.",
        "summary_zh": "当前宏观快照整体偏向风险偏好。",
        "defensive_count": 0,
        "latest_prices": {"BTC": 65000, "QQQ": 440}
    }
    cursor.execute(
        "INSERT INTO macro_signal_snapshots (snapshot_key, verdict, bullish_count, total_count, signals_json, meta_json, source_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (f"macro:{created_at}", "bullish", 2, 3, json.dumps(signals), json.dumps(meta), json.dumps({"source": "manual"}), created_at)
    )

    print("Inserting dummy ETF flows...")
    etfs = [
        {"symbol": "IBIT", "price_change_pct": 2.1, "direction": "inflow", "estimated_flow_score": 15.5, "as_of": created_at},
        {"symbol": "FBTC", "price_change_pct": 1.9, "direction": "inflow", "estimated_flow_score": 12.0, "as_of": created_at}
    ]
    summary = {"direction": "inflow", "summary": "BTC ETF flow leans positive.", "tracked_count": 2, "is_estimated": True}
    cursor.execute(
        "INSERT INTO etf_flow_snapshots (snapshot_key, summary_json, etfs_json, created_at) VALUES (?, ?, ?, ?)",
        (f"etf:{created_at}", json.dumps(summary), json.dumps(etfs), created_at)
    )

    print("Inserting dummy stock analysis...")
    symbols = ["NVDA", "AAPL", "TSLA"]
    for symbol in symbols:
        analysis = {
            "symbol": symbol,
            "current_price": 200.0,
            "signal": "buy",
            "signal_score": 4.5,
            "trend_status": "bullish",
            "support_levels": [190.0],
            "resistance_levels": [210.0],
            "bullish_factors": ["Strong earnings", "High momentum"],
            "risk_factors": ["Valuation"],
            "summary": f"{symbol} shows strong bullish momentum.",
            "as_of": created_at
        }
        cursor.execute(
            """
            INSERT INTO stock_analysis_snapshots (
                symbol, market, analysis_id, current_price, currency, signal,
                signal_score, trend_status, support_levels_json, resistance_levels_json,
                bullish_factors_json, risk_factors_json, summary_text, analysis_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (symbol, "us-stock", f"{symbol}:{created_at}", 200.0, "USD", "buy", 4.5, "bullish", 
             json.dumps([190.0]), json.dumps([210.0]), json.dumps(["Strong earnings"]), json.dumps(["Valuation"]),
             analysis["summary"], json.dumps(analysis), created_at)
        )

    conn.commit()
    conn.close()
    print("✅ Dummy data populated successfully!")

if __name__ == "__main__":
    populate_dummy_data()
