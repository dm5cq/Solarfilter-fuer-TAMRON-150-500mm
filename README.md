# Solarfilter-Aufsatz für Tamron 150-500 mm F5-6.7 Di III VC VXD (A057)

3D-druckbarer Halter für Solarfolie zwischen zwei Plexiglasplatten (200 × 200 mm, je 2 mm), aufgesteckt auf die
Original-Gegenlichtblende **HA057** (Außen-Ø vorne am Gummiring gemessen: 113,05 mm).
Das Filterpaket hält magnetisch am Träger und lässt sich für die Totalität mit einem Griff abnehmen.
Für den Transport haften Frontdeckel und Rückdeckel ebenfalls magnetisch am Filterpaket.

Autor: **Stefan J. Kaiser DM5CQ / OE8KKS** · Material: PETG-CF · Konstruktion mit Unterstützung von Claude (Anthropic)

![Vorschau](bilder/solarfilter_vorschau.png)

![Schutzdeckel](bilder/schutzdeckel_vorschau.png)

## Zwei Varianten

Beide Varianten sind vollständig und gleichwertig – sie unterscheiden sich nur in **Träger** und **Rückrahmen**
(Lage der 8 Magnettaschen an der Trennfuge Filterpaket ↔ Träger). Alle anderen Teile sind identisch.

| | Variante A – Magnete außen | Variante B – Magnete innen |
|---|---|---|
| Ordner | [`stl/variante_A_magnete_aussen`](stl/variante_A_magnete_aussen) | [`stl/variante_B_magnete_innen`](stl/variante_B_magnete_innen) |
| Träger | Taschen offen zur Filterseite, Magnet bündig | Taschen offen zur Kameraseite, 0,6 mm Haut zur Filterseite |
| Rückrahmen | Taschen offen zum Träger, Magnet bündig | Taschen offen zur Plexi-Seite, 0,6 mm Haut zum Träger |
| Magnete | müssen eingeklebt werden | Rückrahmen: von Plexi + Frontrahmen eingeschlossen, Kleben optional; Träger: einkleben empfohlen |
| Haltekraft | maximal (Magnet auf Magnet) | etwas geringer (1,2 mm Abstand), Trennfuge glatt |
| Druck | beliebige Schichthöhe | 0,2 mm Schichthöhe (Haut = 3 Schichten) |

![Magnete Variante B](bilder/magnet_v5_schnitt.png)

## Teile (je Variante im Ordner `stl/variante_…`)

| Datei | Funktion | Drucklage |
|---|---|---|
| `solarfilter_traeger.stl` | bleibt auf der GLB: Flansch mit 8 Magnettaschen (A/B siehe oben) + U-Taschen für Muttern, geschlitztes Rohr Ø114,05 | Flansch aufs Bett |
| `solarfilter_frontrahmen.stl` | Sonnenseite, Tasche 201 × 201 × 5 mm für Plexi / Folie / Plexi, 4 Magnete in den Ecken | Sonnenseite aufs Bett |
| `solarfilter_rueckrahmen.stl` | hinterer Rahmen, 8 Magnettaschen (A/B siehe oben), Zentrierring | Plexi-Seite aufs Bett |
| `solarfilter_schutz_frontdeckel.stl` | Transportschutz vorne, magnetisch (4 Magnete), Zapfen im Fenster | Außenseite aufs Bett |
| `solarfilter_schutz_rueckdeckel.stl` | Transportschutz hinten, magnetisch | Magnetseite aufs Bett |
| `solarfilter_passring.stl` | nur Passprobe auf der GLB (wird nicht eingebaut) | beliebig |

Kein Stützmaterial nötig. PETG-CF → gehärtete Düse; 3–4 Wände, 10–25 % Infill. Druckbett ≥ 216 × 216 mm.

## Zusatztool: Hebelwerkzeug

Zum Abhebeln der Filtereinheit vom Träger: Griff Ø20 × 50 mm mit Lanyard-Bohrung und eingedrucktem Magnet
(Ø10 × 3), Spachtel 18 × 23 × 1,5 mm mittig. Liegend gedruckt, 3MF mit eingebetteten Einstellungen
(100 % Infill, 6 Wände, Druckpause für den Magneten) → [`zubehoer/hebelwerkzeug`](zubehoer/hebelwerkzeug)

<img src="zubehoer/hebelwerkzeug/hebelwerkzeug_vorschau.png" width="500">

## Zubehör

- 8 × M3x15 + 8 × M3-Mutter (Filterpaket verschrauben, Köpfe auf der Sonnenseite)
- 32 × Neodym-Magnet Ø10 × 3 mm, eingeklebt
  - 8 Träger + 8 Rückdeckel: alle **gleich** gepolt · 8 Rückrahmen: **Gegenpol** zur Trennfuge
  - 4 Frontrahmen (stehen 1 mm vor) + 4 Frontdeckel (sitzen unten in der 4,2 mm tiefen Tasche): zueinander **gegenpolig**
- Klettband für die Nut am Rohr (Sicherung gegen Abfallen)
- 2 × Plexiglas 200 × 200 × 2 mm, Solarfolie (z. B. Baader AstroSolar)

## Aufbau

Sonne → Frontrahmen → Plexi → Folie → Plexi → Rückrahmen ‖ *Magnet-Trennfuge* ‖ Träger → Gegenlichtblende → Objektiv

Transport: Frontdeckel ‖ Filterpaket ‖ Rückdeckel (oder statt Rückdeckel der Träger) – alles magnetisch.

## Anpassen

`solarfilter_gen.py` erzeugt alle STLs neu (nur `numpy`, `scipy`, `matplotlib`):

```
python3 solarfilter_gen.py stl/variante_A_magnete_aussen A
python3 solarfilter_gen.py stl/variante_B_magnete_innen  B
```

Wichtige Parameter oben im Skript: `GLB_D`, `SPIEL_D`, `STAPEL`, `MAG_D`/`MAG_H`, `SCHR_LAENGE`, `ZAPFEN_SP`.

## Versionen (Ordner `versionen/`)

| Version | Inhalt |
|---|---|
| v0 | Ausgangsmodell (Rahmen, Deckrahmen, Träger für Objektiv-Ø93) – als ZIP |
| v1 | Plexi-Folie-Plexi-Tasche 5 mm, Träger mit Flansch + Federzungen-Rohr für GLB Ø113,05, Passring |
| v2a | Magnet-Schnellwechsel: Rückrahmen mit 8 Magneten + Zentrierring, Einschmelzmuttern |
| v2b | M3x15 mit Muttern, U-Taschen im Träger, Flansch 5 mm |
| v3 | Transport-Schutzdeckel vorne (Klemmzapfen) und hinten (magnetisch) |
| v4 | Frontdeckel magnetisch: je 4 Magnete in Frontrahmen und Frontdeckel, Frontdeckel 6 mm – **= Variante A** |
| v5 | Magnettaschen Träger zur Kameraseite, Rückrahmen zur Innenseite (0,6 mm Haut) – **= Variante B** |

## Lizenz

[![CC BY-NC-SA 4.0](https://img.shields.io/badge/Lizenz-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.de)

**CC BY-NC-SA 4.0** – siehe [`LICENSE.md`](LICENSE.md). Nachbauen und Verändern erlaubt, mit Namensnennung
(Stefan J. Kaiser DM5CQ / OE8KKS), **nicht kommerziell** und Weitergabe nur unter gleichen Bedingungen.

## ⚠️ Sicherheit

Niemals ohne intakte, zertifizierte Solarfolie in die Sonne schauen oder fotografieren. Folie vor jedem Einsatz gegen
helles Licht auf Löcher prüfen. Das Plexiglas schützt nur mechanisch, es filtert nicht. Filter immer zusätzlich gegen
Abfallen sichern. Nutzung auf eigene Gefahr.
