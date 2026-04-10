# Momentum-Strategie: Top 10--15 Aktien im S&P 500

## Ziel

Auswahl der 10--15 besten Aktien basierend auf: - Frühen, aber
bestätigten Trends - Momentum - Trendstärke - Stabilität

------------------------------------------------------------------------

## Definition von „Top-Aktien"

Top-Aktien = Aktien mit dem höchsten Score basierend auf: - Momentum
(3M, 6M, 12-1) - Trendstärke (ADX, TSI, Regression) -
Trendbeschleunigung (quadratische Regression) - Stabilität (Volatilität)

------------------------------------------------------------------------

## Wichtige Konzepte

### Momentum

-   12-1 Momentum (letzte 12 Monate ohne letzten Monat)
-   3M + 6M Returns kombinieren

### Trendstärke

-   ADX \> 20
-   steigender TSI
-   positive Regressionssteigung

### Trendbeschleunigung

Quadratische Regression: - a \> 0 → Beschleunigung - b \> 0 →
Aufwärtstrend

### Stabilität

-   Niedrige Volatilität bevorzugen

------------------------------------------------------------------------

## Beispiel Score

Score =\
0.40 \* Momentum +\
0.25 \* Trend +\
0.20 \* Acceleration +\
0.15 \* Stability

------------------------------------------------------------------------

## Filterregeln

-   Kurs \> 50 MA
-   Kurs \> 200 MA
-   Abstand zu MA50 \< 15 %
-   Marktfilter: S&P 500 über 200 MA

------------------------------------------------------------------------

## Einstiegssignale

-   Breakout über 20-Tage-Hoch
-   steigender ADX
-   steigender TSI

------------------------------------------------------------------------

## ZigZag Indikator

-   Filtert kleine Bewegungen
-   Zeigt Swing Highs / Lows
-   Parameter z. B. 8 %
-   Repaintet → eher Analyse als Signal

------------------------------------------------------------------------

## Python-Implementierung (ZigZag)

Siehe Chat-Code: - erkennt Swing Highs (1) - erkennt Swing Lows (-1)

------------------------------------------------------------------------

## Wöchentlicher Workflow

1.  Daten laden\
2.  Indikatoren berechnen\
3.  Score berechnen\
4.  Top 10--15 auswählen\
5.  Portfolio rebalancen

------------------------------------------------------------------------

## Wichtige Erkenntnisse

-   Momentum funktioniert, weil Kapital Trends folgt
-   Frühe Trends sind am profitabelsten
-   Kombination mehrerer Faktoren ist robuster als Einzelindikatoren
-   Risikofilter sind entscheidend

------------------------------------------------------------------------

## Fazit

Die beste Strategie kombiniert: - Momentum - Trendbestätigung -
Trendbeschleunigung - Risikokontrolle
