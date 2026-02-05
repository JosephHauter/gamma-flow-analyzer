🦅 TITAN Guardian — SPX Gamma Exposure Intelligence Engine
<img width="624" height="759" alt="image" src="https://github.com/user-attachments/assets/03c4fa87-d9ea-400d-b783-f78d8f1721ee" />


TITAN Guardian is a real-time SPX Gamma Exposure (GEX) analysis and strategy engine that converts live options data into actionable intraday trade context and delivers it directly to Discord with charts, alerts, and regime-aware strategy suggestions.

This is not a dashboard.
This is a decision engine designed for 0DTE / intraday SPX traders.

🚀 What This Project Does

TITAN Guardian continuously:

Pulls live SPY options chain data

Converts it into a synthetic SPX options surface
[//]: # (Title)
# 🦅 TITAN Guardian — SPX Gamma Exposure Intelligence Engine

TITAN Guardian is a real-time SPX Gamma Exposure (GEX) analysis and strategy engine that converts live options data into actionable intraday trade context and delivers it directly to Discord with charts, alerts, and regime-aware strategy suggestions.

This is not a dashboard — it's a decision engine designed for 0DTE / intraday SPX traders.

## 🚀 What this project does

TITAN Guardian continuously:

- pulls live SPY options chain data
- converts it into a synthetic SPX options surface
- calculates Greeks at scale (Gamma, Delta, Vanna, Charm)
- builds exposure profiles by strike
- identifies call walls, put walls and the gamma magnet (zero-crossing)
- classifies market regime (long vs short gamma)
- sends structured Discord alerts, multi-panel exposure charts and context-aware strategy guidance

All of the above runs automatically during market hours.

## 🧠 Core concepts (why this exists)

Most traders:

- look at static GEX levels
- ignore time decay
- miss late-day gamma collapse
- don’t adjust for SPX / SPY basis

TITAN fixes those gaps.

Key philosophy:

- Gamma is dynamic
- Walls move
- Late-day ≠ morning
- SPX ≠ SPY × 10 (without correction)

This project explicitly models those realities.

## ⚙️ System architecture

SPY Options Chain (yfinance)
→ Synthetic SPX Price Engine
→ Greek Calculation Engine
→ Exposure Aggregation by Strike
→ Wall / Magnet Detection
→ Market Regime Classification
→ Strategy Recommendation
→ Discord Alerts + Charts

## 🔧 Major components explained

### 1) Basis Engine (SPX / SPY price fix)

SPX does not equal SPY × 10.

This engine:

- pulls recent SPY & SPX closes
- calculates the cost-of-carry basis
- applies it to all live pricing

Example (concept):

```
live_spx_proxy = (live_spy * 10) + BASIS_OFFSET
```

This prevents misaligned walls and fake magnets.

### 2) Dynamic time-to-expiry engine

Instead of assuming a static expiry:

- time to expiry updates every scan
- correctly reflects 0DTE decay
- automatically returns 0 after market close

This is critical for handling gamma explosion near close and charm acceleration late in the day.

### 3) Greek calculation engine

For every relevant strike, TITAN computes Delta, Gamma, Vanna and Charm using a Black–Scholes framework with dividend adjustment, interest rate input and intraday time decay.

A late-day gamma clamp prevents mathematical blow-ups in the final hour.

### 4) Exposure engine

Each Greek is converted into dollar exposure:

| Metric | Meaning |
|--------|---------|
| GEX | Gamma Exposure (pinning vs acceleration) |
| DEX | Delta Exposure (directional pressure) |
| VEX | Vanna Exposure (volatility-price interaction) |
| CEX | Charm Exposure (dealer delta decay) |

Put exposure is signed negative to preserve directionality.

### 5) Adaptive strike window (late-day fix)

After 2:00 PM EST the strike range narrows aggressively. Focus shifts from global walls to local combat and magnet detection becomes tighter. This prevents irrelevant far-OTM walls from polluting late-day signals.

### 6) Wall detection logic

- Call Wall = strike with max positive GEX
- Put Wall = strike with max negative GEX
- Strength is expressed as % of total absolute GEX

Dominance example:

- 🐮 Bulls +2.4x
- 🐻 Bears +1.8x

### 7) Gamma magnet detection

The Gamma Magnet is identified where GEX flips from negative → positive. The closest valid zero-crossing to price wins. This often marks pinning behavior, chop centers and reversion targets.

### 8) Market regime engine

Based on net GEX:

- 🟢 Long Gamma → mean reversion / range
- 🔴 Short Gamma → momentum / expansion

The regime directly controls strategy logic.

### 9) Strategy recommendation engine

TITAN adapts recommendations by time of day, wall distance, wall strength, gamma regime and trap conditions.

Examples:

- 🛑 Opening chaos → Wait
- 🦅 Lunch chop → Iron Condors
- 🧱 Wall fade → Credit spreads
- 🚀 Wall break → Momentum
- ⚡ Short gamma → Directional scalps

No static strategies — everything is contextual.

## 📊 Visualization engine

Every update includes a 4‑panel chart: Gamma Exposure, Delta Exposure, Vanna Exposure and Charm Exposure, with a current price marker and strike-aligned bars. Charts are dark-mode optimized and auto-uploaded to Discord.

## 🔔 Discord integration

Required webhooks:

- Main Webhook → signals & charts
- Error Webhook → crash alerts & startup pings

On failure the bot sends a 🚨 critical error alert and stops safely. Manual restart is required by design.

## Quick start

1. Clone the repo:

```
git clone <repo-url>
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Create a `.env` file with your webhooks:

```
DISCORD_WEBHOOK_URL=your_main_webhook
ERROR_WEBHOOK_URL=your_error_webhook
```

4. Run (choose one):

- On Windows (double-clickable):

```powershell
.\run_main.bat
```

- From PowerShell / CMD (preferred, runs the package in src):

```powershell
python -m titan_guardian
```

- Legacy: `python main.py` still works — it runs the package shim.

## Development & Windows (required Python version)

This project is developed and tested with Python 3.14.2. Please install Python 3.14.2 and use that interpreter for development and production runs.

Create and activate a virtual environment (Windows examples):

- Create venv using the Python 3.14 installer / py launcher:

```powershell
py -3.14 -m venv venv
```

- Install dependencies into the venv:

```powershell
.\\venv\\Scripts\\Activate.ps1    # PowerShell (may need ExecutionPolicy change)
py -3.14 -m pip install -r requirements.txt
```

- Or using CMD:

```cmd
venv\Scripts\activate.bat
py -3.14 -m pip install -r requirements.txt
```

Notes:
- If you have multiple Python versions, use the `py` launcher with `-3.14` to pick Python 3.14.x. Confirm with `py -3.14 --version` or `python --version` after activation.
- On some systems the exact `-3.14` alias may vary; if `py -3.14` is not available, use the full executable path to your Python 3.14.2 installation.

Using the Windows launcher (`run_main.bat`)

- Double-click `run_main.bat` in Explorer to run the app using the venv (if present) or system Python.
- From PowerShell/CMD:

```powershell
.\run_main.bat
```

Scheduling the launcher with Task Scheduler (Windows)

1. Open Task Scheduler (Win → type "Task Scheduler").
2. Select "Create Task..." (not "Create Basic Task...") for full control.
3. On the "General" tab:
	- Give it a name (e.g., "TITAN Guardian Runner").
	- Choose "Run whether user is logged on or not" if you want background execution.
	- Check "Run with highest privileges" if required.
4. On the "Triggers" tab: create a trigger (e.g., Daily at market open, or At log on).
5. On the "Actions" tab: create a new action:
	- Action: Start a program
	- Program/script: Browse to the `run_main.bat` file (e.g., `C:\path\to\gamma-flow-analyzer\run_main.bat`).
	- Start in (optional): the repository folder (e.g., `C:\path\to\gamma-flow-analyzer`).
6. On "Conditions" / "Settings" set options as desired (for intraday runs you may want to stop the task if it runs longer than X hours).
7. Save the task. If you selected "Run whether user is logged on or not" you'll be prompted for credentials.

Tips:
- If your `.bat` relies on the venv, ensure the venv folder path is correct in `run_main.bat` and the account running the task has access to it.
- Use the Task Scheduler History or log to debug start failures. A common fix is to set the "Start in" field to the repo folder so relative paths resolve correctly.

## ⏱️ Runtime behavior

- Runs every 5 minutes
- Automatically exits after market close
- Designed for intraday only (manual restart required each session)

## ⚠️ Important notes

- Data comes from yfinance (not tick-perfect)
- This is decision support, not financial advice

Best used with:

- SPX options
- 0DTE strategies
- Discretionary execution

## 🧩 Who this is for

- ✅ SPX / 0DTE traders
- ✅ Gamma-aware discretionary traders
- ✅ Quant-curious retail traders
- ❌ Long-term investors
- ❌ Fully automated execution systems

## 🦅 Final thought

TITAN Guardian isn’t about predicting price. It’s about knowing where dealers are trapped, where price is pinned, when gamma flips, and when not to trade.

Trade less. Trade smarter.

---

Non A.I text starting here :p -

Might not update anymore as I've moved to more live data and have created a new system which I'm using for everyday algo trading. This is my old system — I thought it would be cool if someone improved upon it or benefited from it!

Issue: Yahoo data has a ~15 minute delay, so it's best not to use this as a sniper for trades or long-term investments. It's more useful for understanding where the market may head in the next ~30 minutes.

DO NOT TRUST this system in the first and final hour of the trading day! This is not financial advice — use only in paper trading until you build and figure out your own edge.
Vanna Exposure
