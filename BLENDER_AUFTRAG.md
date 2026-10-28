# Auftrag: Filmisches Hintergrundvideo mit Blender

Lies zuerst `CLAUDE.md` in diesem Ordner, vor allem den Abschnitt „Das Hintergrundvideo“. Dort steht, wie das
jetzige Video entstanden ist und was Tobias daran stört.

## Ziel

Das Hintergrundvideo der Einstiegsseite (https://roleplay.tobiaszwilling.me) soll aussehen wie **ein kurzer
Ausschnitt aus einem Actionfilm** in dunkler Fantasy, nicht wie ein bewegtes Standbild. Gebaut wird es in
**Blender** (Open Source), gesteuert per Python-Skript (`bpy`, Blender im Hintergrund ohne Oberfläche), damit es
nachvollziehbar und wiederholbar bleibt.

## Vorgaben von Tobias

- **Keine KI-Videogeneratoren** (auch nicht Higgsfield) und **keine Stockvideos**.
- Erlaubt: Blender, freie 3D-Modelle, Texturen und HDRIs mit klarer Lizenz, am liebsten CC0
  (Poly Haven, Quaternius, Kenney, ambientCG). **Jede Quelle mit Lizenz in `CREDITS.md` festhalten.**
  Nichts mit unklarer Lizenz, keine Figuren oder Orte aus bekannten Filmen und Spielen.
- Stimmung wie bisher: dunkle Fantasy, warmes Gold gegen kühles Blau-Violett, Nebel, Glut, ein leuchtendes Tor,
  ein Wanderer im Umhang. Die Szene darf aber neu erfunden werden.
- Wirkung „Actionfilm“: echte Kamerafahrten, 3–4 Einstellungen mit Schnitten in etwa 12–15 Sekunden
  (zum Beispiel Totale → Fahrt auf das Tor → Nah auf den Wanderer → Lichtausbruch), Bewegungsunschärfe,
  Tiefenunschärfe, Lichtstrahlen im Nebel, Funken, eventuell leichtes Kamerawackeln oder Breitbild-Look.

## Technische Anforderungen (die Seite muss danach ohne Umbau weiterlaufen)

- Zwei Fassungen mit denselben Dateinamen wie bisher, in `assets/`:
  - `hero-16x9.mp4` (1920×1080, Querformat): Tor bzw. Blickpunkt **rechts**, links bleibt dunkler Raum für den Text.
  - `hero-9x16.mp4` (1080×1920, Hochformat): Hauptmotiv **oben**, untere Hälfte dunkel für den Text.
  - Dazu `poster-16x9.jpg` und `poster-9x16.jpg` (ein starkes Standbild aus dem Video).
- H.264, ohne Ton, `-movflags +faststart`, **je höchstens ca. 3 MB**, damit die Seite schnell lädt.
- Das Video läuft als Schleife (`loop`). Entweder nahtlos, oder der Schnitt vom Ende zum Anfang wirkt wie ein
  gewollter Filmschnitt. Mit Tobias besprechen, was besser aussieht.
- Filmkorn liefert die Seite per CSS. Nicht ins Video einbauen, das bläht die Datei auf.
- Die alten Dateien vorher sichern (zum Beispiel nach `assets/alt/`), nicht einfach überschreiben.
- Den Blender-Code in einen eigenen Ordner legen, zum Beispiel `blender/`, mit Skript zum Neu-Rendern.
  Die alte Shader-Szene in `scene/` bleibt stehen.

## Arbeitsweise

- Mit Tobias auf Deutsch, einfach, ohne Denglisch. Er programmiert nicht selbst, er entscheidet.
- **Installation:** Blender ist noch nicht installiert (Stand 28.10.2026). Es ist groß (deutlich über 1 GB).
  **Vorher sagen, was wohin kommt**, und erst nach Tobias' Okay installieren. Danach Pfad und Größe (`du -sh`)
  melden und eintragen in
  `~/.claude/projects/-Users-tobiaszwilling-Downloads/memory/installations-protokoll.md`.
  Heruntergeladene Modelle in einen eigenen Ordner (zum Beispiel `blender/assets/`), Größe ebenfalls melden.
- **In kleinen Schritten mit Bildern arbeiten:**
  1. Zuerst 2–3 Varianten als Skizze beschreiben (Einstellungen, Kamerafahrt, Handlung) und Tobias
     eine wählen lassen.
  2. Dann pro Einstellung **Standbilder** rendern und zeigen, bevor das ganze Video gerendert wird.
  3. Dann eine kurze Vorschau in niedriger Auflösung, erst danach das finale Rendern.
- Renderzeiten im Blick behalten. Lange Renderläufe in abbrechbare, fortsetzbare Blöcke teilen (Einzelbilder
  rendern und vorhandene überspringen). Eevee bevorzugen, Cycles nur wenn es sich deutlich lohnt.
- Am Ende auf der Seite prüfen: lokal mit `python3 -m http.server 8765` im Projektordner, Rechner- und
  Handybreite, Text gut lesbar über dem Video, Dateigrößen, Schleife.
- Jeden Schritt sofort in `CLAUDE.md` unter „Verlauf“ und „Offen“ nachtragen.
- Committen ist in Ordnung. **Pushen (= live schalten) erst, wenn Tobias das fertige Video gesehen und
  freigegeben hat.**
