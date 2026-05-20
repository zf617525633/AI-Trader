import sys
import os
import json
from datetime import datetime

# Setup paths to import project modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'service/server'))

from database import get_db_connection

def generate_html_chart(limit=100):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch latest records first, then reverse them for chronological order in chart
    cursor.execute(f"SELECT profit, total_value, recorded_at FROM profit_history ORDER BY recorded_at DESC LIMIT {limit}")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No data available.")
        return

    # Reverse to make it chronological
    rows = rows[::-1]

    labels = [row['recorded_at'] for row in rows]
    profits = [row['profit'] for row in rows]
    values = [row['total_value'] for row in rows]

    current_profit = profits[-1]
    profit_class = "profit-pos" if current_profit >= 0 else "profit-neg"
    profit_prefix = "+" if current_profit >= 0 else ""

    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI-Trader Profit Dashboard (Last {limit})</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }}
        h1 {{ margin-top: 0; color: #38bdf8; font-size: 24px; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #334155; padding: 20px; border-radius: 12px; }}
        .stat-label {{ font-size: 14px; color: #94a3b8; margin-bottom: 5px; }}
        .stat-value {{ font-size: 28px; font-weight: bold; }}
        .profit-pos {{ color: #10b981; }}
        .profit-neg {{ color: #ef4444; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>AI-Trader: Agent_001 Performance (Last {limit} Points)</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Asset Value</div>
                <div class="stat-value">${values[-1]:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Net Profit/Loss</div>
                <div class="stat-value {profit_class}">
                    {profit_prefix}{current_profit:,.2f} USD
                </div>
            </div>
        </div>

        <canvas id="profitChart"></canvas>
    </div>

    <script>
        const ctx = document.getElementById('profitChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'Net Profit (USD)',
                    data: {json.dumps(profits)},
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#38bdf8'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: '#334155' }},
                        ticks: {{ color: '#94a3b8', maxRotation: 45, minRotation: 45 }}
                    }},
                    y: {{
                        grid: {{ color: '#334155' }},
                        ticks: {{ color: '#94a3b8' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
    """

    output_path = os.path.join(current_dir, "pnl_chart_latest.html")
    with open(output_path, "w") as f:
        f.write(html_template)
    print(output_path)

if __name__ == "__main__":
    generate_html_chart(100)
