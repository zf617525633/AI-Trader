import sys
import time
import os
import requests
import math
from datetime import datetime

# Setup paths to import project modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'service/server'))

try:
    from price_fetcher import _get_hyperliquid_mid_price, get_price_from_market
    from database import get_db_connection
except ImportError as e:
    print(f"Failed to import project modules: {e}")
    sys.exit(1)

# Configuration
AGENT_ID = 2
TOKEN = "KiPiTI9vE3gHWQiv9oEvSYlbVbR4hLObPRMpC7Fdmvk"
API_BASE_URL = "http://localhost:8000/api"
INITIAL_CASH = 100000.0

# TP/SL Thresholds
TP_THRESHOLD = 0.03  # 3%
SL_THRESHOLD = -0.03 # -3%

LOG_FILE = os.path.join(current_dir, "pnl_monitor.log")

def sell_position(symbol, market, quantity, current_price, reason):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = {
        "market": market,
        "action": "sell",
        "symbol": symbol,
        "price": current_price if market == 'us-stock' else 0, 
        "quantity": quantity,
        "content": f"Automated {reason} triggered at ${current_price:,.2f}. (TP: 3%, SL: -3%)",
        "executed_at": "now" if market != 'us-stock' else datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    try:
        resp = requests.post(f"{API_BASE_URL}/signals/realtime", json=payload, headers=headers)
        data = resp.json()
        if data.get("success"):
            return True, data.get("price")
        return False, data.get("detail") or data.get("message")
    except Exception as e:
        return False, str(e)

def monitor():
    with open(LOG_FILE, "a") as f:
        f.write(f"\n--- [RESTARTED] Multi-Asset Risk Management at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    
    while True:
        try:
            headers = {"Authorization": f"Bearer {TOKEN}"}
            resp = requests.get(f"{API_BASE_URL}/positions", headers=headers)
            pos_data = resp.json()
            
            if "positions" not in pos_data:
                time.sleep(60)
                continue

            positions = pos_data.get("positions", [])
            current_cash = pos_data.get("cash", 100000.0)
            
            total_position_value = 0
            log_entries = []
            all_prices_valid = True
            
            for pos in positions:
                symbol = pos['symbol']
                market = pos['market']
                quantity = pos['quantity']
                entry_price = pos['entry_price']
                
                # Get current price
                current_price = None
                if market == 'crypto':
                    current_price = _get_hyperliquid_mid_price(symbol)
                else:
                    # For US stocks, try fetch, fallback to cached price in position
                    current_price = get_price_from_market(symbol, 'now', market) or pos.get('current_price')
                
                if current_price:
                    total_position_value += current_price * abs(quantity)
                    pnl_pct = (current_price - entry_price) / entry_price
                    if pos['side'] == 'short':
                        pnl_pct = (entry_price - current_price) / entry_price
                    
                    status_msg = f"[{symbol}] ${current_price:,.2f} ({pnl_pct:+.2f}%)"
                    
                    # Check TP/SL
                    if pnl_pct >= TP_THRESHOLD:
                        success, exec_price = sell_position(symbol, market, abs(quantity), current_price, "Take Profit")
                        if success: status_msg += f" -> TP Sold @ ${exec_price:,.2f}"
                    elif pnl_pct <= SL_THRESHOLD:
                        success, exec_price = sell_position(symbol, market, abs(quantity), current_price, "Stop Loss")
                        if success: status_msg += f" -> SL Sold @ ${exec_price:,.2f}"
                    
                    log_entries.append(status_msg)
                else:
                    # CRITICAL: If we can't get a price for even one position, 
                    # we must NOT save this record to DB as it will skew the total value.
                    all_prices_valid = False
                    break

            if all_prices_valid:
                total_value = current_cash + total_position_value
                profit = total_value - INITIAL_CASH
                
                # Update Profit History
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO profit_history (agent_id, total_value, cash, position_value, profit, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (AGENT_ID, total_value, current_cash, total_position_value, profit, datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')))
                conn.commit()
                conn.close()
                
                if log_entries:
                    full_log = f"[{datetime.now().strftime('%H:%M:%S')}] " + " | ".join(log_entries) + f" | Total: ${total_value:,.2f}\n"
                    with open(LOG_FILE, "a") as f:
                        f.write(full_log)
                        f.flush()
            else:
                with open(LOG_FILE, "a") as f:
                    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Price fetch failed for some assets. Skipping DB record to avoid data corruption.\n")

        except Exception as e:
            with open(LOG_FILE, "a") as f:
                f.write(f"Error at {datetime.now()}: {str(e)}\n")
                f.flush()
        
        time.sleep(60)

if __name__ == "__main__":
    monitor()
