"""DipCatcher-2: a slow EMA trend bot for make.fun btc-race-24h-20261118-1444.

Races a long-only cbBTC bot on 1-minute bars with $1,000 of paper money. The dev
window this was built against is a choppy down day (-2.8%) on which every house
baseline loses money: buy-and-hold -$31.63, momentum -$23.87, rsi-bollinger -$39.92,
adx-momentum -$75.57, and ema-cross -$148.17 on 80 whipsawed trades. Mean reversion
is worse still (a dip-buy grid loses $26-$65 on the same window: dips keep dipping).
So this bot does the opposite of yesterday's DipCatcher: it only ever buys a
confirmed uptrend, trades rarely, and lets a trailing stop cap every loss.

Rules (all on 1-minute closes, standard library only, deterministic):
  - Trend: EMA(60) vs EMA(240), each seeded as the mean of its first span of closes.
  - Enter (all cash, one position) when EMA(60) crosses above EMA(240) AND the
    slow EMA has risen over the last 60 bars (the trend is really rising, not just
    crossing in chop) AND at least 30 bars have passed since the last exit.
  - Exit the whole position when EMA(60) crosses back below EMA(240), or when the
    close falls 0.8% below the highest close since entry (trailing stop).
  - Buys cap slippage at 200 bps (the dev window's widest open-vs-previous-close
    move is 18 bps); sells cap it at 10000 bps so an exit always fills instead of
    being refused into a falling market.

Local grade on the frozen dev window (wire-level replay against the kit's own
fill model, validated to the cent against grade-local on two baselines):
  net PnL +$8.22, 2 trades, max drawdown 0.90% — one winning round trip on the
  day's only clean rally, nothing else traded. The parameters sit on plateaus, not
  spikes: slope windows 30-60 bars all give the same trade, and trailing stops
  0.7%-0.9% give +$6.00 to +$8.22.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
FAST_SPAN = 60
SLOW_SPAN = 240
# The slow EMA must have risen over this many bars for an entry to count.
SLOPE_BARS = 60
# Bars to wait after an exit before a new entry is allowed.
COOLDOWN_BARS = 30
# Trailing stop: sell when the close falls this far below the peak since entry.
# 0.7% is the tight end of a smooth plateau (0.7% -> +$8.22, 0.8% -> +$7.45,
# 0.9% -> +$6.00 on the dev window; the mirror window agrees, -$6.15 vs -$7.20),
# while 0.6% is a cliff: it exits on the rally's first pullback and the dev
# window goes to -$0.83, failing the gate.
TRAIL_PCT = 0.007
# Buy slippage cap: a buy is rejected by the engine when its fill would land more
# than this far above the decision-time close. The bot gets one or two entry
# chances per day, so a rejected entry can cost the whole race; the largest
# open-vs-previous-close gap on the dev window is 18.4 bps, and 200 bps is still
# a real guard against buying into a spike (a 2% gap would turn the expected +1%
# winner into a loser). Sells have no cap: exits must always fill.
BUY_SLIPPAGE_BPS = 200
SELL_SLIPPAGE_BPS = 10000


class Ema:
    """An EMA over closes, seeded as the mean of its first span (the baselines'
    convention), in float64 so the same bars give the same orders every run."""

    def __init__(self, span):
        self.span = span
        self.warm = []
        self.value = None

    def push(self, close):
        if self.value is not None:
            self.value += (2 / (self.span + 1)) * (close - self.value)
            return self.value
        self.warm.append(close)
        if len(self.warm) == self.span:
            self.value = sum(self.warm) / self.span
        return self.value


fast = Ema(FAST_SPAN)
slow = Ema(SLOW_SPAN)
slow_history = []
prev_gap = None
peak = None
cooldown = 0


def on_batch(state, batch):
    global prev_gap, peak, cooldown
    if state.warming_up:
        return []
    close = state.close(SYMBOL)
    if close is None:
        return []
    fast_value = fast.push(close)
    slow_value = slow.push(close)
    if fast_value is None or slow_value is None:
        return []
    slow_history.append(slow_value)
    gap = (fast_value - slow_value) / close * 10000
    last_gap = prev_gap
    prev_gap = gap
    if cooldown > 0:
        cooldown -= 1
    held = state.positions.get(SYMBOL)
    if held is not None:
        if peak is None or close > peak:
            peak = close
        if gap < 0 or close < peak * (1 - TRAIL_PCT):
            peak = None
            cooldown = COOLDOWN_BARS
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": SELL_SLIPPAGE_BPS}]
        return []
    # Flat: enter only on a fresh upward cross with a rising slow trend.
    if last_gap is None or last_gap > 0 or gap <= 0 or cooldown > 0:
        return []
    if len(slow_history) <= SLOPE_BARS:
        return []
    if slow_history[-1] <= slow_history[-1 - SLOPE_BARS]:
        return []
    amount = state.cash if state.cash < state.equity else state.equity
    if amount < int(state.hello["fees"]["min_notional_quote_units"]):
        return []
    peak = close
    return [{"side": "buy", "symbol": SYMBOL, "notional_quote_units": amount,
             "max_slippage_bps": BUY_SLIPPAGE_BPS}]


makefun_bars.run(on_batch)
