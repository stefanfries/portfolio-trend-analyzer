# 📊 Algorithmus zur technischen Einstiegserkennung für Trendfolge (Optionsscheine)

## 🧠 Ziel

Automatisierbare Logik zur Bestimmung von:

- Trend (Long/No Trade)
- Entscheidenden Marken (Support/Resistance)
- Einstiegssignalen (Breakout / Pullback)
- Risiko (Trendbruch)
- Timing-Score

---

# 1️⃣ Trendfilter

## Regel:

- EMA50 > EMA200 → Nur Long-Setups erlaubt
- Kurs > EMA50 → kurzfristig bullish
- Kurs > EMA200 → strukturell bullish

## Python:

```python
trend_is_up = ema50[-1] > ema200[-1] and close[-1] > ema50[-1]
```

---

# 2️⃣ Support & Resistance

## Methode (einfach):

```python
resistance = max(close[-20:])
support = min(close[-20:])
```

## Methode (Swing Points):

```python
def find_swings(prices, window=3):
    highs = []
    lows = []
    for i in range(window, len(prices)-window):
        if prices[i] == max(prices[i-window:i+window]):
            highs.append((i, prices[i]))
        if prices[i] == min(prices[i-window:i+window]):
            lows.append((i, prices[i]))
    return highs, lows
```

---

# 3️⃣ Breakout-Logik

## Regel:

- Close > Resistance + 0.5%
- Volumen über Durchschnitt
- Momentum positiv

## Python:

```python
breakout = (
    close[-1] > resistance * 1.005 and
    volume[-1] > volume[-20:].mean() and
    close[-1] > close[-5:].mean()
)
```

---

# 4️⃣ Pullback-Logik

## Regel:

- Kurs nahe EMA50 (+/- 2%)
- Trend intakt

## Python:

```python
pullback = (
    close[-1] <= ema50[-1] * 1.02 and
    close[-1] >= ema50[-1] * 0.98 and
    trend_is_up
)
```

---

# 5️⃣ Trendbruch (Exit / Vermeidung)

## Regel:
- Kurs < letztes Swing Low

## Python:
```python
trend_break = close[-1] < last_swing_low
```

---

# 6️⃣ Timing-Score

## Logik:
```python
score = 0

if trend_is_up:
    score += 3

if abs(close[-1] - support) / support < 0.02:
    score += 2

if breakout:
    score += 3
elif pullback:
    score += 2

if trend_break:
    score -= 3
```

---

# 📊 Interpretation

| Score | Bedeutung |
|------|----------|
| 8–10 | Perfekter Einstieg |
| 6–7  | Beobachten / kleiner Einstieg |
| 4–5  | Neutral |
| <4   | Vermeiden |

---

# 🔥 Anwendung für Optionsscheine

## Gute Setups:

- Breakout + Volumen → schnelle Gewinne
- Pullback im Trend → optimaler Einstieg

## Schlechte Setups:

- Seitwärtsmarkt → Theta-Verlust
- Unter Support → Trendbruch-Risiko

---

# 🏁 Fazit

Dieser Algorithmus ermöglicht:

- Vollautomatische Einstiegserkennung
- Kombination mit Optionsschein-Scoring
- Systematisches Trading ohne Bauchgefühl
