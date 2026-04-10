# Optionsschein-Screening- und Auswahl-Algorithmus

## Überblick

Dieser Algorithmus dient dazu, trendstarke Aktien zu identifizieren und passende Call-Optionsscheine systematisch auszuwählen. Er ist speziell für eine Trendfolge-Strategie ausgelegt.

---

# Teil 1: Screening-Logik (Python-tauglich)

## Schritt 1: Trend-Screener (Underlying)

Ziel: Identifikation von Aktien mit stabilem Aufwärtstrend.

### Kriterien

- Kurs über SMA50
- SMA50 über SMA200
- Positives Momentum (5 Tage)
- ADX > 20
- Kurs über Supertrend

### Implementierung

```python
def trend_score(df):
    score = 0

    # Trendrichtung
    if df["close"].iloc[-1] > df["sma50"].iloc[-1]:
        score += 1
    if df["sma50"].iloc[-1] > df["sma200"].iloc[-1]:
        score += 1

    # Momentum
    if df["close"].pct_change(5).iloc[-1] > 0:
        score += 1

    # Trendstärke
    if df["adx"].iloc[-1] > 20:
        score += 1

    # Supertrend
    if df["close"].iloc[-1] > df["supertrend"].iloc[-1]:
        score += 1

    return score
```

### Filterbedingung

```python
if trend_score(df) >= 4:
    candidate = True
```

---

## Schritt 2: Optionsschein-Filter

Ziel: Auswahl geeigneter Call-Optionsscheine.

### Zielparameter

- Delta: 0.4 – 0.7
- Moneyness: -5% bis +5%
- Restlaufzeit: > 60 Tage
- Geringer Spread

---

### Moneyness berechnen

```python
def moneyness(underlying_price, strike):
    return (underlying_price - strike) / strike
```

---

### Restlaufzeit berechnen

```python
from datetime import datetime

def days_to_expiry(expiry_date):
    return (expiry_date - datetime.now()).days
```

---

### Optionsschein-Score

```python
def option_score(option, underlying_price):
    score = 0

    m = moneyness(underlying_price, option["strike"])
    dte = days_to_expiry(option["expiry"])

    # Delta
    if 0.4 <= option["delta"] <= 0.7:
        score += 2

    # Moneyness
    if -0.05 <= m <= 0.05:
        score += 2
    elif -0.1 <= m <= 0.1:
        score += 1

    # Laufzeit
    if dte > 90:
        score += 2
    elif dte > 60:
        score += 1

    # Spread
    if option["spread_pct"] < 0.02:
        score += 1

    return score
```

---

### Auswahl des besten Optionsscheins

```python
best_option = max(options, key=lambda x: option_score(x, underlying_price))
```

---

# Teil 2: Automatische Auswahl von Optionsscheinen

## Datenstruktur eines Optionsscheins

```python
{
    "name": "...",
    "strike": 100,
    "expiry": datetime,
    "bid": 1.2,
    "ask": 1.3,
    "delta": 0.52,
    "iv": 0.25,
    "type": "call"
}
```

---

## Delta-Approximation (falls nicht vorhanden)

```python
import numpy as np
from scipy.stats import norm

def approx_delta(S, K, T, r=0.01, sigma=0.3):
    d1 = (np.log(S/K) + (r + 0.5 * sigma**2)*T) / (sigma*np.sqrt(T))
    return norm.cdf(d1)
```

---

## Pipeline zur Auswahl

```python
def find_best_option(underlying, options):
    underlying_price = underlying["price"]
    enriched_options = []

    for opt in options:
        if "delta" not in opt:
            opt["delta"] = approx_delta(
                S=underlying_price,
                K=opt["strike"],
                T=days_to_expiry(opt["expiry"]) / 365
            )

        opt["spread_pct"] = (opt["ask"] - opt["bid"]) / opt["ask"]

        enriched_options.append(opt)

    best = max(enriched_options, key=lambda x: option_score(x, underlying_price))

    return best
```

---

# Integration in eine Trading-Pipeline

## Stage 1

- Aktien nach Trend filtern

## Stage 2

- Optionsscheine abrufen
- Scoring anwenden
- Besten auswählen

## Stage 3

- Optional: Bewertung durch LLM (Chance/Risiko, Timing)

---

# Wichtige Praxis-Regeln

- Spread < 2% bevorzugen
- Laufzeit > 60 Tage
- Delta im Bereich 0.4 – 0.7
- Keine extrem hohe implizite Volatilität
- Liquidität ist wichtiger als maximaler Hebel

---

# Fazit

Der Algorithmus kombiniert:

- Technische Trendanalyse
- Optionsbewertung (Delta, Moneyness, Laufzeit)
- Systematisches Scoring

Er eignet sich besonders für eine strukturierte, automatisierte Trendfolge-Strategie mit Optionsscheinen.
