import sys
import os

# Setup paths to import project modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'service/server'))

from database import get_db_connection

def generate_ascii_chart():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT profit, recorded_at FROM profit_history ORDER BY recorded_at ASC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No data available.")
        return

    profits = [row['profit'] for row in rows]
    times = [row['recorded_at'].split('T')[1][:5] for row in rows] # Extract HH:MM

    min_p = min(profits)
    max_p = max(profits)
    range_p = max_p - min_p if max_p != min_p else 1

    height = 10
    width = len(profits)

    print("\n--- Profit Trend (USD) ---")
    for y in range(height, -1, -1):
        threshold = min_p + (y / height) * range_p
        line = f"{threshold:8.2f} | "
        for p in profits:
            if p >= threshold:
                line += " * "
            else:
                line += "   "
        print(line)
    
    print(" " * 11 + "-" * (width * 3))
    print(" " * 11 + "".join([f"{t} " for t in times]))
    print("\n--------------------------")

if __name__ == "__main__":
    generate_ascii_chart()
