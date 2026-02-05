import sys
import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import io
import os
from dotenv import load_dotenv 
from scipy.stats import norm
from datetime import datetime, timedelta
import pytz

# ===== CONFIGURATION =====
load_dotenv() 

# 1. Main Content Webhook (From .env)
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
ERROR_WEBHOOK_URL = os.getenv('ERROR_WEBHOOK_URL')

# 3. Manual Offset (Safety Valve)
# If price is still off by 5 points, set this to 5.0
MANUAL_OFFSET = 0.0

if not WEBHOOK_URL:
    print("❌ ERROR: No Main Webhook found! Check .env file.")
    sys.exit(1)

# ===== ERROR REPORTER =====
def send_crash_alert(error_msg):
    try:
        timestamp = datetime.now(pytz.timezone('US/Eastern')).strftime('%I:%M:%S %p')
        payload = {
            "content": f"🚨 **TITAN CRITICAL FAILURE** | `{timestamp}`\n"
                       f"**ERROR:** `{error_msg}`\n"
                       f"⚠️ *The bot has stopped. Please restart manually.*"
        }
        requests.post(ERROR_WEBHOOK_URL, json=payload)
        print("📨 Error Alert Sent to Discord.")
    except Exception as e:
        print(f"Failed to send error alert: {e}")

# ===== BASIS ENGINE (The Price Fix) =====
def calculate_basis_offset():
    print("⚙️ Calibrating SPX/SPY Basis (Interest Rate Correction)...")
    try:
        spy_hist = yf.Ticker("SPY").history(period="5d")
        spx_hist = yf.Ticker("^SPX").history(period="5d")
        
        last_close_spy = spy_hist["Close"].iloc[-2]
        last_close_spx = spx_hist["Close"].iloc[-2]
        
        # Calculate the points difference (Cost of Carry)
        basis = last_close_spx - (last_close_spy * 10)
        
        print(f"✅ DETECTED BASIS: +{basis:.2f} points")
        return basis
    except Exception as e:
        err_text = f"Basis Calculation Failed: {e}"
        print(f"⚠️ {err_text}")
        # We do NOT kill the bot for this, just default to 0
        return 0.0

# Initialize Basis ONCE
BASIS_OFFSET = calculate_basis_offset()

# ===== TIME ENGINE =====
def get_dynamic_time_to_expiry():
    ny_tz = pytz.timezone('US/Eastern')
    now = datetime.now(ny_tz)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    if now > market_close: return 0
    minutes_remaining = (market_close - now).total_seconds() / 60
    return max(1, minutes_remaining) / (390 * 252)

# ===== MATH ENGINE =====
def calculate_greeks(S, K, T, r, sigma, q, option_type):
    if T <= 0 or sigma <= 0 or S <= 0: return 0, 0, 0, 0
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_neg_d1 = norm.cdf(-d1)
    
    if option_type == "call":
        delta = np.exp(-q * T) * cdf_d1
        charm = -np.exp(-q * T) * (pdf_d1 * (2*(r-q)*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T)) - q * cdf_d1)
    else:
        delta = np.exp(-q * T) * (cdf_d1 - 1)
        charm = -np.exp(-q * T) * (pdf_d1 * (2*(r-q)*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T)) + q * cdf_neg_d1)
    
    gamma = np.exp(-q * T) * pdf_d1 / (S * sigma * np.sqrt(T))
    vanna = -np.exp(-q * T) * pdf_d1 * d2 / sigma
    return delta, gamma, vanna, charm

def get_market_data():
    print("Fetching Market Data...")
    for attempt in range(3):
        try:
            spy = yf.Ticker("SPY")
            spy_data = spy.history(period="1d", interval="1m")
            if spy_data.empty: raise ValueError("No SPY Data")
            live_spy = spy_data["Close"].iloc[-1]
            
            # === APPLY BASIS OFFSET (The Price Fix) ===
            live_spx_proxy = (live_spy * 10) + BASIS_OFFSET + MANUAL_OFFSET
            
            expiries = spy.options
            if not expiries: raise ValueError("No Expiries")
            chain = spy.option_chain(expiries[0])
            
            return live_spx_proxy, chain
        except Exception as e:
            print(f"Attempt {attempt+1}/3 Failed: {e}")
            time.sleep(2)
    return None

# ===== STRATEGY ENGINE =====
def get_strategy_suggestion(regime_val, call_dist, put_dist, call_str_pct, put_str_pct, hour):
    if hour < 10: return "🛑 OPENING CHAOS: Wait for structure."
    if 11.5 <= hour < 14:
        if regime_val > 0: return "🦅 LUNCH CHOP: Iron Condors favored."
        else: return "⚠️ LUNCH TRAP: Tighten stops."

    if call_dist < 0 and put_dist < 0: return "🛑 TRAP ZONE: Walls Inverted."
    if abs(call_dist) > 40 and abs(put_dist) > 40 and abs(regime_val) < 500000000: return "🛑 NO EDGE: Walls too far."

    if call_dist < 0: return "🚀 CALL WALL BROKEN: Momentum Longs"
    if put_dist < 0: return "📉 PUT WALL BROKEN: Momentum Shorts"

    if call_dist < 15 and call_str_pct > 10: return "🛡️ RESISTANCE FADE: Credit Call Spread"
    if put_dist < 15 and put_str_pct > 10: return "🛡️ SUPPORT BOUNCE: Credit Put Spread"

    if regime_val > 0: return "🦅 LONG GAMMA: Range Trade / Mean Reversion"
    return "⚡ SHORT GAMMA: Directional Scalps"

def process_data():
    T = get_dynamic_time_to_expiry()
    if T == 0: return "CLOSED"

    data_pkg = get_market_data()
    if not data_pkg: return None
    spx_price, chain = data_pkg
    
    r, q = 0.04, 0.0
    rows = []
    
    # === LATE DAY CLAMP (The Fix) ===
    # After 14:00 (2 PM), we narrow the view.
    # We stop looking at "Global" walls and focus only on "Local" combat.
    ny_tz = pytz.timezone('US/Eastern')
    current_hour = datetime.now(ny_tz).hour
    
    if current_hour >= 14: # After 2 PM
        range_mult = 0.005 # Tight Focus (0.5% range ~35 points)
        # Force the "Magnet" check to be tighter too
    else:
        range_mult = 0.05 # Normal Broad View (5% range)
        
    strike_min = spx_price * (1 - range_mult)
    strike_max = spx_price * (1 + range_mult)
    
    for df, is_call in [(chain.calls, True), (chain.puts, False)]:
        opt_type = "call" if is_call else "put"
        for _, row in df.iterrows():
            strike_raw = row["strike"]
            if strike_raw < strike_min or strike_raw > strike_max: continue

            oi = row.get("openInterest", 0)
            vol = row.get("volume", 0) 
            iv = row.get("impliedVolatility", 0)
            
            if oi < 100: continue 

            effective_oi = oi 
            
            if effective_oi > 0 and iv > 0:
                adjusted_strike_view = (strike_raw * 10) + BASIS_OFFSET
                
                delta, gamma, vanna, charm = calculate_greeks(spx_price, adjusted_strike_view, T, r, iv, q, opt_type)
                
                # === GEX DECAY FIX ===
                # As T -> 0, Gamma explodes to infinity for ATM strikes.
                # We dampen this mathematical explosion to prevent "Fake Walls" right at the price.
                if T < 0.002: # Last hour
                    gamma = gamma * 0.5 
                
                gex = gamma * effective_oi * 100 * (spx_price**2) * 0.01
                dex = delta * effective_oi * 100 * spx_price
                vex = vanna * effective_oi * 100 * spx_price * 0.01
                cex = charm * effective_oi * 100 * spx_price / 365
                
                if not is_call: gex *= -1
                
                final_strike_label = int(round(adjusted_strike_view / 5) * 5)
                rows.append({"strike": final_strike_label, "GEX": gex, "DEX": dex, "VEX": vex, "CEX": cex})

    if not rows: return None
    
    df = pd.DataFrame(rows)
    df_agg = df.groupby("strike").sum().reset_index()
    
    total_net_gex = df_agg['GEX'].sum()
    total_abs_gex = df_agg['GEX'].abs().sum()
    total_net_charm = df_agg['CEX'].sum()
    
    try:
        if total_abs_gex == 0: raise ValueError("Zero GEX")
        call_wall_row = df_agg.loc[df_agg['GEX'].idxmax()]
        put_wall_row = df_agg.loc[df_agg['GEX'].idxmin()]
        call_wall = int(call_wall_row['strike'])
        put_wall = int(put_wall_row['strike'])
        
        call_strength_pct = (abs(call_wall_row['GEX']) / total_abs_gex) * 100
        put_strength_pct = (abs(put_wall_row['GEX']) / total_abs_gex) * 100
        safe_put_str = max(put_strength_pct, 0.1)
        safe_call_str = max(call_strength_pct, 0.1)
        
        if call_strength_pct > put_strength_pct:
            dom_score = call_strength_pct / safe_put_str
            dom_label = f"🐮 Bulls +{dom_score:.1f}x"
        else:
            dom_score = put_strength_pct / safe_call_str
            dom_label = f"🐻 Bears +{dom_score:.1f}x"
    except:
        call_wall = int(spx_price); put_wall = int(spx_price)
        call_strength_pct = 0; put_strength_pct = 0; dom_label = "Neutral"

    df_sorted = df_agg.sort_values("strike")
    magnet = spx_price
    min_diff = float('inf')
    gex_vals = df_sorted['GEX'].values
    strikes = df_sorted['strike'].values
    
    for i in range(len(df_sorted)-1):
        if (gex_vals[i] < 0 and gex_vals[i+1] > 0):
            strike = strikes[i+1]
            dist = abs(strike - spx_price)
            if dist < min_diff:
                min_diff = dist
                magnet = int(strike)
                
    final_min = min(spx_price - 50, put_wall - 25)
    final_max = max(spx_price + 50, call_wall + 25)
    df_final = df_agg[(df_agg["strike"] >= final_min) & (df_agg["strike"] <= final_max)].sort_values("strike")
    
    metrics = {
        "regime_val": total_net_gex, "net_charm": total_net_charm,
        "call_str": call_strength_pct, "put_str": put_strength_pct,
        "call_dist": call_wall - spx_price, "put_dist": spx_price - put_wall,
        "dom_label": dom_label
    }
    return df_final, spx_price, call_wall, put_wall, magnet, metrics


def get_strength_label(pct):
    if pct > 20: return "🔥 MAJOR"
    if pct > 10: return "💪 Strong"
    return "☁️ Weak"

def generate_charts(df, spx_price):
    plt.style.use('dark_background')
    fig, axs = plt.subplots(2, 2, figsize=(18, 10))
    fig.suptitle(f'SPX GEX TITAN GUARDIAN - ${spx_price:.2f}', fontsize=22, color='white', y=0.96)
    
    charts = [ (axs[0, 0], 'GEX', 'Gamma Exposure'), (axs[0, 1], 'DEX', 'Delta Exposure'),
               (axs[1, 0], 'VEX', 'Vanna Exposure'), (axs[1, 1], 'CEX', 'Charm Exposure') ]
    
    for ax, col, title in charts:
        colors = ['#00FF00' if x >= 0 else '#FF0000' for x in df[col]]
        ax.bar(df['strike'].astype(str), df[col], color=colors, width=0.6, zorder=2)
        ax.set_title(title, fontsize=12, color='white', pad=10)
        strikes = df['strike'].values
        if len(strikes) > 0:
            x_pos = np.interp(spx_price, strikes, np.arange(len(strikes)))
            ax.axvline(x=x_pos, color='white', linestyle='--', linewidth=1.5, alpha=0.6, zorder=3)
            ax.text(x_pos, ax.get_ylim()[1] * 0.9, f'{spx_price:.2f}', color='black', fontsize=9, 
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.9), ha='center')
        ax.grid(color='gray', linestyle=':', linewidth=0.5, alpha=0.3)
        ax.set_xticks(range(len(df['strike']))); ax.set_xticklabels(df['strike'], rotation=90, fontsize=9)
        ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    plt.subplots_adjust(hspace=0.4, bottom=0.15)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0); plt.close()
    return buf

def main():
    print("🦅 TITAN GUARDIAN ONLINE (Offset + Crash Logs).")
    print("Press Ctrl+C to stop.")
    
    # Send a Startup Ping to confirm Error Webhook works
    try:
        requests.post(ERROR_WEBHOOK_URL, json={"content": "✅ **TITAN SYSTEM STARTED**"})
    except:
        print("⚠️ Warning: Error Webhook failed to ping.")

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Running Scan...")
            result = process_data()
            if result == "CLOSED": 
                print("Market Closed. Exiting.")
                break

            if result:
                df, price, call_wall, put_wall, magnet, met = result
                ny_tz = pytz.timezone('US/Eastern'); now_est = datetime.now(ny_tz)
                time_str = now_est.strftime('%I:%M %p EST'); current_hour = now_est.hour + (now_est.minute / 60) 
                
                status_line = "🟢 STABLE (Long Gamma)" if met['regime_val'] > 0 else "🔴 VOLATILE (Short Gamma)"
                dom_icon = "📈" if "Bulls" in met['dom_label'] else "📉" if "Bears" in met['dom_label'] else "⚖️"
                c_str_lab = get_strength_label(met['call_str']); p_str_lab = get_strength_label(met['put_str'])
                raw_strategy = get_strategy_suggestion(met['regime_val'], met['call_dist'], met['put_dist'], met['call_str'], met['put_str'], current_hour)
                
                if "NO EDGE" in raw_strategy: strat_box = f"RECOMMENDED: 🛑 SIT OUT\nREASON: {raw_strategy.split(': ')[1]}"
                elif "CHAOS" in raw_strategy: strat_box = f"RECOMMENDED: 🛑 WAIT\nMODE: {raw_strategy.split(': ')[1]}"
                elif "LUNCH" in raw_strategy: strat_box = f"RECOMMENDED: 🍔 PATIENCE\nMODE: {raw_strategy.split(': ')[1]}"
                elif "TRAP" in raw_strategy: strat_box = f"RECOMMENDED: 🛑 TRAP DETECTED\nMODE: {raw_strategy.split(': ')[1]}"
                elif "BROKEN" in raw_strategy: strat_box = f"RECOMMENDED: 🚀 MOMENTUM\nMODE: Breakout Follow-Through"
                elif "CREDIT" in raw_strategy: strat_box = f"RECOMMENDED: 🛡️ CREDIT SPREADS\nPLAY: Fade the Wall"
                elif "LONG GAMMA" in raw_strategy: strat_box = "RECOMMENDED: 🦅 IRON CONDOR\nPLAY: Range / Mean Reversion"
                else: strat_box = "RECOMMENDED: ⚡ DIRECTIONAL SCALPS\nPLAY: Debit Spreads / Long Options"
                
                alert_header = ""
                alerts = []
                if now_est.hour >= 14: alerts.append("⚠️ LATE DAY: Gamma Decaying Fast"); alerts.append("👀 CHECK CHARM CHART")
                if alerts: alert_header = f"> **ALERTS**\n> {' '.join(alerts)}\n\n"

                text_msg = (
                    f"🦅 **TITAN GUARDIAN** | 🕒 `{time_str}`\n\n"
                    f"**CONDITION:** `{status_line}`\n"
                    f"**CONTROL:** `{dom_icon} {met['dom_label']}`\n"
                    f"**PRICE:** `${price:.2f}` (Offset: +{BASIS_OFFSET:.1f})\n\n"
                    f"{alert_header}"
                    f"📡 **KEY LEVELS**\n"
                    f"🧱 **Call Wall:** `{call_wall}` ({c_str_lab})\n"
                    f"🧱 **Put Wall:** `{put_wall}` ({p_str_lab})\n"
                    f"🧲 **Magnet:** `{magnet}`\n\n"
                    f"🧠 **AI STRATEGY**\n"
                    f"```yaml\n{strat_box}\n```"
                    f"ℹ️ *System Safe + Price Fix*"
                )
                
                r = requests.post(WEBHOOK_URL, json={"content": text_msg})
                if r.status_code == 204:
                    img_buf = generate_charts(df, price)
                    requests.post(WEBHOOK_URL, files={"file": ("titan_intel.png", img_buf, "image/png")})
                    print(f"Update Sent: {time_str}")
                else: print(f"Discord Error: {r.status_code}")
            time.sleep(300)
        except KeyboardInterrupt: 
            print("\nShutting down...")
            break
        except Exception as e: 
            # === CRASH ALERT TRIGGER ===
            print(f"Critical Error: {e}")
            send_crash_alert(str(e))
            time.sleep(60)

if __name__ == "__main__":
    main()
    sys.exit(0)