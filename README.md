🦅 TITAN Guardian — SPX Gamma Exposure Intelligence Engine

TITAN Guardian is a real-time SPX Gamma Exposure (GEX) analysis and strategy engine that converts live options data into actionable intraday trade context and delivers it directly to Discord with charts, alerts, and regime-aware strategy suggestions.

This is not a dashboard.
This is a decision engine designed for 0DTE / intraday SPX traders.

🚀 What This Project Does

TITAN Guardian continuously:

Pulls live SPY options chain data

Converts it into a synthetic SPX options surface

Calculates Greeks at scale (Gamma, Delta, Vanna, Charm)

Builds exposure profiles by strike

Identifies:

🧱 Call Walls

🧱 Put Walls

🧲 Gamma Magnet (zero-crossing)

🧠 Market regime (long vs short gamma)

Sends:

Structured Discord alerts

Multi-panel exposure charts

Context-aware strategy guidance

All of this runs automatically during market hours.

🧠 Core Concepts (Why This Exists)

Most traders:

Look at static GEX levels

Ignore time decay

Miss late-day gamma collapse

Don’t adjust for SPX / SPY basis

TITAN fixes that.

Key Philosophy

Gamma is dynamic

Walls move

Late-day ≠ morning

SPX ≠ SPY × 10 (without correction)

This engine explicitly models those realities.

⚙️ System Architecture
SPY Options Chain (yfinance)
        ↓
Synthetic SPX Price Engine
        ↓
Greek Calculation Engine
        ↓
Exposure Aggregation by Strike
        ↓
Wall / Magnet Detection
        ↓
Market Regime Classification
        ↓
Strategy Recommendation
        ↓
Discord Alerts + Charts

🔧 Major Components Explained
1️⃣ Basis Engine (SPX / SPY Price Fix)

SPX does not equal SPY × 10.

This engine:

Pulls recent SPY & SPX closes

Calculates the cost-of-carry basis

Applies it to all live pricing

live_spx_proxy = (live_spy * 10) + BASIS_OFFSET


This prevents misaligned walls and fake magnets.

2️⃣ Dynamic Time-to-Expiry Engine

Instead of assuming a static expiry:

Time to expiry updates every scan

Correctly reflects 0DTE decay

Automatically returns 0 after market close

This is critical for:

Gamma explosion near close

Charm acceleration late day

3️⃣ Greek Calculation Engine

For every relevant strike, TITAN computes:

Delta

Gamma

Vanna

Charm

Using a Black-Scholes framework with:

Dividend adjustment

Interest rate input

Intraday time decay

A late-day gamma clamp prevents mathematical blow-ups in the final hour.

4️⃣ Exposure Engine

Each Greek is converted into dollar exposure:

Metric	Meaning
GEX	Gamma Exposure (pinning vs acceleration)
DEX	Delta Exposure (directional pressure)
VEX	Vanna Exposure (volatility-price interaction)
CEX	Charm Exposure (dealer delta decay)

Put exposure is signed negative to preserve directionality.

5️⃣ Adaptive Strike Window (Late-Day Fix)

After 2:00 PM EST:

Strike range narrows aggressively

Focus shifts from global walls → local combat

Magnet detection becomes tighter

This prevents irrelevant far-OTM walls from polluting late-day signals.

6️⃣ Wall Detection Logic

Call Wall = strike with max positive GEX

Put Wall = strike with max negative GEX

Strength is expressed as % of total absolute GEX

Dominance label example:

🐮 Bulls +2.4x
🐻 Bears +1.8x

7️⃣ Gamma Magnet Detection

The Gamma Magnet is identified where:

GEX flips from negative → positive

Closest valid zero-crossing to price wins

This often marks:

Pinning behavior

Chop centers

Reversion targets

8️⃣ Market Regime Engine

Based on net GEX:

🟢 Long Gamma → mean reversion / range

🔴 Short Gamma → momentum / expansion

This regime directly controls strategy logic.

9️⃣ Strategy Recommendation Engine

TITAN adapts recommendations by:

Time of day

Wall distance

Wall strength

Gamma regime

Trap conditions

Examples:

🛑 Opening chaos → Wait

🦅 Lunch chop → Iron Condors

🧱 Wall fade → Credit spreads

🚀 Wall break → Momentum

⚡ Short gamma → Directional scalps

No static strategies. Everything is contextual.

📊 Visualization Engine

Every update includes a 4-panel chart:

Gamma Exposure

Delta Exposure

Vanna Exposure

Charm Exposure

With:

Current price marker

Strike-aligned bars

Dark-mode optimized visuals

Charts are auto-uploaded to Discord.

🔔 Discord Integration
Required Webhooks

Main Webhook → signals & charts

Error Webhook → crash alerts & startup pings

On failure, the bot:

Sends a 🚨 critical error alert

Stops safely

Requires manual restart (by design)
1. git clone this bad boy 😮‍💨

2. Install Dependencies
pip install -r requirements.txt

3. Create .env
DISCORD_WEBHOOK_URL=your_main_webhook
ERROR_WEBHOOK_URL=your_error_webhook

4. Run
python main.py

⏱️ Runtime Behavior

Runs every 5 minutes

Automatically exits after market close

Designed for intraday only

Manual restart required each session

⚠️ Important Notes

Data comes from yfinance (not tick-perfect)

This is decision support, not financial advice

Best used with:

SPX options

0DTE strategies

Discretionary execution

🧩 Who This Is For

✅ SPX / 0DTE traders
✅ Gamma-aware discretionary traders
✅ Quant-curious retail traders
❌ Long-term investors
❌ Fully automated execution systems

🦅 Final Thought

TITAN Guardian isn’t about predicting price.

It’s about knowing:

Where dealers are trapped

Where price is pinned

When gamma flips

When not to trade

Trade less. Trade smarter.

Non A.I text starting here :p -
Might not update anymore as ive come to more live data and have created a new system which im using for everyday algo trading. This is my old system i thought it would be cool if someone improved upon it or benefited from it! 
Issue is yahoo data delay of 15 min i believe so its best not to use this as a sniper for trades or long term investments but for knowing where the market is headed in the next 30 min or so.
DO NOT TRUST this system in the first and final hour of trading day! this is not financial advice use only in paper trading until you build and figure out your own edge!!
