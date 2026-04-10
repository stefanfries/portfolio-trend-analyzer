```python
# optionsschein_scoring.py
import pandas as pd

# Beispiel-Daten (kann aus CSV/API geladen werden)
data = [
    {"WKN": "MM3GS6", "Basiswert": "Alphabet Inc.", "Typ": "Call", "Basispreis": 350, "KursBasiswert": 273.76, "Delta": 0.279, "Hebel": 22.65, "Omega": 6.35, "Moneyness": 0.78, "Aufgeld": 32.24, "ImplVol": 34.4, "Theta": -0.005},
    {"WKN": "MG2FJW", "Basiswert": "Amazon.com Inc.", "Typ": "Call", "Basispreis": 210, "KursBasiswert": 199.34, "Delta": 0.450, "Hebel": 17.49, "Omega": 7.91, "Moneyness": 0.95, "Aufgeld": 11.04, "ImplVol": 39.2, "Theta": -0.0086},
    # weitere 17 Scheine hier analog
]

# DatenFrame erstellen
df = pd.DataFrame(data)

# Scoring-Funktion
def score_schein(row):
    score = 0
    # Moneyness 0.9-1.1 optimal
    if 0.9 <= row['Moneyness'] <= 1.1:
        score += 2
    elif 0.85 <= row['Moneyness'] < 0.9 or 1.1 < row['Moneyness'] <= 1.15:
        score += 1

    # Delta 0.4-0.7 optimal
    if 0.4 <= row['Delta'] <= 0.7:
        score += 2
    elif 0.3 <= row['Delta'] < 0.4 or 0.7 < row['Delta'] <= 0.8:
        score += 1

    # Hebel / Omega > 6 attraktiv
    if row['Hebel'] > 10 or row['Omega'] > 6:
        score += 1

    # Aufgeld < 25% bevorzugt
    if row['Aufgeld'] < 25:
        score += 1

    # Implizite Volatilität moderat 25-50%
    if 25 <= row['ImplVol'] <= 50:
        score += 1

    # Theta möglichst klein
    if abs(row['Theta']) < 0.01:
        score += 1

    return score

# Scoring anwenden
df['Score'] = df.apply(score_schein, axis=1)

# Scheine sortieren nach Score absteigend
filtered_df = df.sort_values(by='Score', ascending=False)

# Optional: nur Scheine mit Score >= 4 anzeigen
top_scheine = filtered_df[filtered_df['Score'] >= 4]

print(top_scheine)
```

