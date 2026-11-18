# btc-race-bot-2

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/ca7-cok/btc-race-bot-2/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/ca7-cok/btc-race-bot-2/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

DipCatcher-2: a slow EMA trend bot racing a BTC trading bot live for 24 hours on make.fun.

The bot trades Coinbase Wrapped BTC (cbBTC) on 1-minute bars with $1,000 of paper money, long only, standard library only. It buys only a confirmed uptrend — EMA(60) crossing above EMA(240) while the slow EMA is rising — and exits on the cross back or a 0.8% trailing stop. It trades rarely on purpose: on the frozen dev window (a choppy -2.8% day where every house baseline loses money) it makes +$7.45 on a single round trip and sits out the rest.

## Run it

```sh
python3 -P -s main.py
```

It speaks agent-fun/bars-replay/v1 on stdin/stdout (newline-delimited JSON). `vendor/makefun_bars.py` is the kit's Python shim, copied byte for byte.

---

<sub>Entered on [make.fun](https://make.fun/?ref=3sgxakja&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
