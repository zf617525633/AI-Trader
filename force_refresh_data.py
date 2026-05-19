import os
import asyncio
import sys
from pathlib import Path

# Add the server directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'service', 'server'))

async def force_refresh():
    import config
    from config import ALPHA_VANTAGE_API_KEY
    
    # Debug info
    config_file = config.__file__
    env_path = Path(config_file).parent.parent.parent / ".env"
    print(f"DEBUG: config.py path: {config_file}")
    print(f"DEBUG: Expected .env path: {env_path}")
    print(f"DEBUG: Does .env exist? {env_path.exists()}")
    
    masked_key = ALPHA_VANTAGE_API_KEY[:4] + "*" * (len(ALPHA_VANTAGE_API_KEY) - 4) if ALPHA_VANTAGE_API_KEY else "None"
    print(f"🚀 Starting manual data refresh with API key: {masked_key}")
    
    from market_intel import (
        refresh_market_news_snapshots,
        refresh_macro_signal_snapshot,
        refresh_etf_flow_snapshot,
        refresh_stock_analysis_snapshots
    )
    
    try:
        print("1. Refreshing Market News...")
        news_res = refresh_market_news_snapshots()
        print(f"   ✅ Done: {news_res.get('inserted_categories', 0)} categories updated.")
        
        print("2. Refreshing Macro Signals...")
        macro_res = refresh_macro_signal_snapshot()
        print(f"   ✅ Done: Verdict is {macro_res.get('verdict')}.")
        
        print("3. Refreshing ETF Flows...")
        etf_res = refresh_etf_flow_snapshot()
        print(f"   ✅ Done: Direction is {etf_res.get('direction')}.")
        
        print("4. Refreshing Stock Analysis...")
        stock_res = refresh_stock_analysis_snapshots()
        print(f"   ✅ Done: {stock_res.get('inserted_symbols', 0)} symbols analyzed.")
        
        print("\n✨ All real data has been successfully fetched and saved to the database!")
        print("You can now refresh your browser to see the real data.")
        
    except Exception as e:
        print(f"\n❌ Error during refresh: {e}")
        print("Hint: Make sure your API key is correct and you have internet access.")

if __name__ == "__main__":
    asyncio.run(force_refresh())
