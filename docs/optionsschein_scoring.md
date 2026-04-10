# Optionsschein Scoring-Logik für Trendfolgestrategie

## Ziel

Diese Logik bewertet Optionsscheine systematisch nach ihrer Eignung für
eine Trendfolgestrategie.

------------------------------------------------------------------------

## Grundprinzip

Ein guter Trendfolge-Optionsschein: - reagiert stark auf Kursbewegungen
(Delta) - hat moderaten Hebel (kein Zockerschein) - enthält idealerweise
inneren Wert - hat geringe Kosten (Spread, Aufgeld)

------------------------------------------------------------------------

## Scoring-Modell

Jeder Schein erhält Punkte in folgenden Kategorien:

### 1. Delta (Gewichtung: 30%)

  Delta                        Punkte
  ---------------------------- --------
  0.5 -- 0.7                   10
  0.4 -- 0.5 oder 0.7 -- 0.8   7
  0.3 -- 0.4                   4
  \< 0.3                       0

------------------------------------------------------------------------

### 2. Hebel (Gewichtung: 20%)

  Hebel      Punkte
  ---------- --------
  4 -- 10    10
  10 -- 15   7
  15 -- 25   4
  \> 25      0

------------------------------------------------------------------------

### 3. Innerer Wert (Gewichtung: 15%)

  Zustand   Punkte
  --------- --------
  \> 0      10
  = 0       0

------------------------------------------------------------------------

### 4. Spread (Gewichtung: 10%)

  Spread    Punkte
  --------- --------
  \< 2%     10
  2 -- 4%   7
  4 -- 6%   4
  \> 6%     0

------------------------------------------------------------------------

### 5. Aufgeld p.a. (Gewichtung: 10%)

  Aufgeld     Punkte
  ----------- --------
  \< 20%      10
  20 -- 30%   7
  30 -- 40%   4
  \> 40%      0

------------------------------------------------------------------------

### 6. Restlaufzeit (Gewichtung: 10%)

  Restlaufzeit    Punkte
  --------------- --------
  \> 9 Monate     10
  6 -- 9 Monate   7
  3 -- 6 Monate   4
  \< 3 Monate     0

------------------------------------------------------------------------

### 7. Implizite Volatilität (Gewichtung: 5%)

  IV          Punkte
  ----------- --------
  \< 40%      10
  40 -- 60%   7
  \> 60%      4

------------------------------------------------------------------------

## Gesamtscore

Gesamtscore = gewichteter Durchschnitt aller Kategorien

Maximal: 10 Punkte

------------------------------------------------------------------------

## Interpretation

  Score     Bewertung
  --------- --------------------------------
  8 -- 10   Sehr gut (Trendfolge geeignet)
  6 -- 8    Gut
  4 -- 6    Mittelmäßig
  \< 4      Ungeeignet

------------------------------------------------------------------------

## Python Implementierung

``` python
from datetime import datetime

def score_option(option):
    score = 0
    weight_sum = 0

    def weighted(points, weight):
        nonlocal score, weight_sum
        score += points * weight
        weight_sum += weight

    # Delta
    d = option["delta"]
    if 0.5 <= d <= 0.7:
        weighted(10, 0.30)
    elif 0.4 <= d < 0.5 or 0.7 < d <= 0.8:
        weighted(7, 0.30)
    elif 0.3 <= d < 0.4:
        weighted(4, 0.30)
    else:
        weighted(0, 0.30)

    # Hebel
    h = option["leverage"]
    if 4 <= h <= 10:
        weighted(10, 0.20)
    elif 10 < h <= 15:
        weighted(7, 0.20)
    elif 15 < h <= 25:
        weighted(4, 0.20)
    else:
        weighted(0, 0.20)

    # Innerer Wert
    weighted(10 if option["intrinsic_value"] > 0 else 0, 0.15)

    # Spread
    s = option["spread"]
    if s < 2:
        weighted(10, 0.10)
    elif s < 4:
        weighted(7, 0.10)
    elif s < 6:
        weighted(4, 0.10)
    else:
        weighted(0, 0.10)

    # Aufgeld p.a.
    p = option["premium_pa"]
    if p < 20:
        weighted(10, 0.10)
    elif p < 30:
        weighted(7, 0.10)
    elif p < 40:
        weighted(4, 0.10)
    else:
        weighted(0, 0.10)

    # Restlaufzeit
    days = (option["expiry"] - datetime.now()).days
    if days > 270:
        weighted(10, 0.10)
    elif days > 180:
        weighted(7, 0.10)
    elif days > 90:
        weighted(4, 0.10)
    else:
        weighted(0, 0.10)

    # IV
    iv = option["iv"]
    if iv < 40:
        weighted(10, 0.05)
    elif iv < 60:
        weighted(7, 0.05)
    else:
        weighted(4, 0.05)

    return round(score / weight_sum, 2)
```

------------------------------------------------------------------------

## Beispiel

``` python
option = {
    "delta": 0.65,
    "leverage": 6,
    "intrinsic_value": 1.2,
    "spread": 1.5,
    "premium_pa": 18,
    "expiry": datetime(2026, 12, 18),
    "iv": 35
}

print(score_option(option))
```

------------------------------------------------------------------------

## Erweiterungen

-   Integration in FastAPI Scanner
-   Ranking aller Scheine
-   Filter: Score \> 7
-   Kombination mit Trend-Indikatoren (Supertrend, SMA)

------------------------------------------------------------------------
