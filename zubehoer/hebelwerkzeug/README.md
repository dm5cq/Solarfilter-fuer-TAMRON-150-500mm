# Zusatztool: Hebelwerkzeug zum Ablösen der Filtereinheit

Kleines Spachtel-Werkzeug, um das magnetisch gehaltene Filterpaket vom Träger abzuhebeln.

![Vorschau](hebelwerkzeug_vorschau.png)

| Maß | Wert |
|---|---|
| Griff | Ø20 × 50 mm, hinten halbkugelig gerundet, vordere Kante R1,5 |
| Lanyard-Bohrung | Ø5 mm, 7 mm vor dem Griffende, quer zur Spachtel |
| Spachtel | 18 × 23 × 1,5 mm, mittig auf der Griffachse, vordere Ecken R4 |
| Anschliff | beidseitig auf 0,6 mm über die vorderen 4 mm |
| Gesamt | 20 × 20,6 × 73 mm |

## Druck

- Drucklage **stehend**: Griffende unten, Spachtel oben
- Stützmaterial nur auf dem Druckbett (unter dem runden Ende); Brim 5–8 mm
- 100 % Infill, eher hohe Drucktemperatur für gute Schichthaftung
- Die Schichten liegen quer zur Spachtel → nur mit dem vorderen Drittel ansetzen und vorsichtig hebeln, bevorzugt an einer Ecke

## Anpassen

```
python3 hebelwerkzeug_gen.py solarfilter_hebelwerkzeug.stl
```

Benötigt `numpy` und `scikit-image`. Parameter (Griff, Spachtel, Anschliff `FASE_L`/`FASE_T`, Lanyard-Bohrung) oben im Skript.
