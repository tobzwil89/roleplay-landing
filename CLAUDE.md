# Projekt: Roleplay-Warteliste (Einstiegsseite)

Filmische Einstiegsseite mit Warteliste für die Rollenspiel-App (`../roleplay`). **Live** unter
https://roleplay.tobiaszwilling.me (GitHub Pages, Repo `tobzwil89/roleplay-landing`, jeder Push auf `main` geht live).
Im Desktop (`../tobiaszwilling-desktop`) mit `embed: false` verlinkt, öffnet im neuen Tab.

## Aufbau

- `index.html` – die ganze Seite: Text DE/EN, Anmeldung, Impressum und Datenschutz als Dialog. Kein Build.
- `assets/hero-16x9.mp4`, `assets/hero-9x16.mp4` – Hintergrundvideo quer/hoch (12 s, nahtlose Schleife).
- `assets/poster-*.jpg` – Standbilder (Ersatz bei „Bewegung reduzieren“ und solange das Video lädt).
- `assets/fonts/` – Cormorant Garamond und Manrope (OFL), lokal statt von Google (Datenschutz).
- `scene/scene.html` – die Szene „Das Tor“ als WebGL-Shader, live im Browser ansehbar.
- `blender/scene.py` – neue Szene „Das Tor erwacht“ in Blender (siehe Kopf des Skripts für den Aufruf).
- `scene/render.mjs` – nimmt die Szene Bild für Bild auf und baut Videos und Standbilder
  (`node scene/render.mjs`, Probe-Standbilder: `node scene/render.mjs still`). Braucht ffmpeg und Playwright
  aus `../tunnel-front/node_modules`.

## Das Hintergrundvideo: wie es gemacht ist

Komplett aus Code, keine KI-Videos, keine fremden Bilder:

1. **Szene als Fragment-Shader** (`scene/scene.html`, reines WebGL2, keine Bibliothek). Jeder Bildpunkt wird
   berechnet: Himmel mit Wolken und Sternen, Berge, Ruinen, Spitzbogen-Tor (zwei Kreise + Rechteck), Stufen,
   Wanderer mit Stab und Schatten, Bodennebel (Rauschen „fbm“), Lichtstrahlen (vom Bildpunkt zur Lichtquelle
   laufen und zählen, wie oft der Durchgang getroffen wird), 70 Glutfunken, Runen-Puls, Tonemapping.
2. **Nahtlose Schleife:** Alles hängt nur von der Phase `uT` (0–1) ab. Bewegungen nutzen ganzzahlige
   Frequenzen; treibender Nebel überblendet zwei versetzte Rauschfelder. Nach 12 s ist das Bild wieder identisch.
3. **Aufnahme:** `scene/render.mjs` öffnet die Szene in Playwright (Chromium), ruft `renderAt(t)` für jedes der
   360 Bilder auf, macht Screenshots, ffmpeg baut daraus H.264-MP4 (CRF 27, ca. 1 MB je Format).
4. **Zwei Formate:** Querformat (Tor rechts, Text links) und Hochformat (Szene kleiner und höher, Text unten).
   Die Seite wählt per `<source media="(orientation: portrait)">`. Filmkorn kommt per CSS, nicht im Video
   (spart Dateigröße).

### Wunsch für später: viel filmischer („wie ein kurzer Actionfilm-Ausschnitt“)

Tobias' Rückmeldung am 28.10.2026: „ist gut für jetzt“, soll aber deutlich cineastischer werden.
Das aktuelle Video ist ein ruhiges Standbild mit Bewegung, ohne Schnitte und echte Kamerafahrt; die
Formen sind flach (2D-Silhouetten). Ideen, grob nach Wirkung:

- **Echtes 3D statt 2D-Shader:** Blender (Open Source) mit freien Modellen (Poly Haven, Quaternius, Kenney, CC0)
  oder Three.js. Erst damit gibt es Tiefe, Licht auf Oberflächen, Perspektive bei Kamerafahrten.
  Wahrscheinlich der größte Sprung. Blender rendert offline, Ergebnis wieder als MP4.
- **Schnitte und Kamera:** 3–4 Einstellungen in 12–15 s (Totale → Fahrt auf das Tor → Nah auf den Wanderer →
  Lichtausbruch), Kameraschwenks, leichtes Wackeln, Zeitlupe.
- **Kinoeffekte:** Bewegungsunschärfe, Tiefenunschärfe, Linsenreflexe, Breitbild-Balken, stärkere Farbgebung,
  Blitze/Funkenregen, Staub im Gegenlicht.
- **Handlung:** z. B. das Tor öffnet sich, Licht flutet heraus, Figur tritt hindurch.
- Schleife ist dann schwerer: entweder Schnitt zurück auf die erste Einstellung oder Video nur einmal abspielen
  und auf dem letzten Bild stehen bleiben.
- Bisher ausgeschlossen auf Tobias' Wunsch: KI-Videogeneratoren (Higgsfield) und Stockvideos.

## Entscheidungen

- Video wird aus Code erzeugt (kein Higgsfield, kein Stockmaterial), auf Tobias' Wunsch.
- Video statt Live-3D auf der Seite: läuft auf jedem Handy gleich, schont Akku.
- Querformat: Tor rechts, Text links. Hochformat: Szene nach oben geschoben, Text unten.
- Warteliste über EmailOctopus (kostenlos bis ca. 2.500 Abonnenten, Daten in Irland). Brevo verworfen (Konto ging
  nicht / nicht kostenlos). Unser eigenes Formular sendet direkt an den EmailOctopus-Endpunkt (`EO_FORM_ACTION`,
  Felder `field_0` und Honeypot) statt deren Skript einzubinden: deren Skript lädt Google reCAPTCHA (Datenschutz)
  und bringt eigenes Aussehen mit.
- Kein fremder Markenname („Character AI“) auf der Seite: Abmahnrisiko bei abwertendem Vergleich.
- Produktname steht noch nicht fest; die Seite kommt ohne Namen aus.

## Verlauf

- 28.10.2026: Szene, Videos (je ca. 1 MB, Schleifennaht gemessen: so glatt wie ein normaler Bildwechsel),
  Seite, Rechtstexte gebaut. Per Playwright geprüft: Rechner (1440×900) und Handy (390×844), DE und EN,
  kein seitliches Verrutschen, keine Konsolenfehler, Formularprüfung funktioniert („startet in Kürze“ ohne Brevo).
  Lokal ansehen: `python3 -m http.server 8765` im Projektordner, dann http://127.0.0.1:8765
  (nicht als Datei öffnen, sonst lädt die Schrift nicht).

- 28.10.2026: Umstieg Brevo → EmailOctopus, Datenschutztext angepasst (Three Hearts Digital Ltd, London; Adresse
  aus deren Datenschutzerklärung von 2020). Verbindung geprüft: Anfrage kommt an, EmailOctopus antwortet mit
  INVALID_PARAMETERS für eine example.com-Testadresse. Unklar, ob wegen der Adresse oder weil reCAPTCHA verlangt wird.
- 28.10.2026: Testanmeldung mit tobitobbs@gmail.com über die Seite erfolgreich (EmailOctopus: success).
  Der frühere Fehler lag an der example.com-Adresse. Doppel-Opt-in war in EmailOctopus aus, Tobias hat es
  eingeschaltet.
- 28.10.2026: Repo auf GitHub (Tobias hat es angelegt, weil das Anlegen für Claude gesperrt war), Pages und
  DNS laufen, Seite live. Desktop-Eintrag committet und gepusht, Klick öffnet neuen Tab (geprüft).

- 28.10.2026: Blender 5.2.3 installiert (/Applications/Blender.app, 907 MB, steht im Installationsprotokoll).
  Tobias wählt Variante A „Das Tor erwacht“ (Totale → Fahrt → Nah über die Schulter → Lichtausbruch, 13 s) und
  einen harten Schnitt vom Ende zurück zum Anfang. Szene komplett aus Code in `blender/scene.py` (keine fremden
  Modelle, siehe `CREDITS.md`). Standbilder je Einstellung gerendert (`blender/stills/quer.jpg`, `hoch.jpg`),
  ca. 6 s je Bild in voller Größe. Wartet auf Tobias' Rückmeldung zu den Standbildern.
  Gelernt: Grundkörper müssen nach außen zeigende Flächen haben, sonst schneidet das Boolean die Toröffnung
  nicht aus. Tiefenunschärfe braucht längeres Objektiv und nahes Vordergrundmotiv, sonst kaum sichtbar.
- 29.10.2026: Anfang heller und packender (Zweig `worktree-anfang-heller`): schnellere Kranfahrt in der Totale
  (tief und weit → hoch und 20 m näher), zwei „Herzschläge“ des Tors (Bild 18 und 58: Runen, Türspalt,
  Lichtkegel und neues Licht „Torglut“ vor dem Tor), Belichtung je Einstellung (Totale +0,7, Fahrt +0,3, ab Nah
  wie bisher; Sprünge auf den Schnitten). Mittlere Helligkeit Totale 28 → 45, Herzschläge 70/73, Finale ~100
  unverändert. Einstellungen 3 und 4 unverändert (nachgemessen). Probebilder: `blender/stills/neu-16x9/`,
  `neu-9x16/`. Gelernt: Puls nur an Runen ist aus der Totale unsichtbar, erst Licht in den Nebel wirkt;
  zu starker Puls macht alles milchig und nimmt dem Finale die Wirkung.
- 29.10.2026: SheepIt (kostenlose Gemeinschafts-Renderfarm, wie AI Horde) angeschaut. Hat Blender 5.2, eigene
  Python-Skripte verboten (für uns egal: `scene.py --save` schreibt eine fertige .blend ohne Skriptbedarf).
  EEVEE-Unterstützung unklar. Hürde: Hochladen erst, nachdem der eigene Rechner 10 Bilder für andere
  gerendert hat (Client nötig). Für dieses Video nicht lohnend (lokal ca. 2 h), Tobias rendert über Nacht lokal.
  Testdatei (alter Stand, 30 Bilder, volle Größe) liegt im Hauptordner unter `blender/sheepit-test-16x9.blend`,
  lokales Vergleichsbild `blender/frames/sheepit-referenz/0015.png` (9,5 s je Bild in voller Größe).

## Offen

- Anmeldung mit eingeschaltetem Doppel-Opt-in testen: kommt die Bestätigungsmail, steht die Adresse bis zum
  Klick auf „Pending“?
- Idee von Tobias (28.10.2026) für eine spätere Fassung: Ein Ritter in voller Rüstung reitet durch einen Wald
  auf eine Burg zu. Fände er cool. Braucht Pferd und Ritter als gute 3D-Modelle mit Reitanimation (freie
  Lizenz) und einen Wald; deutlich aufwendiger als die jetzige Szene. **Dafür SheepIt nutzen** (lokal würde
  das Stunden dauern): vorher 10 Bilder mit dem SheepIt-Client für andere rendern (GPU/Metal, Kerne und RAM
  begrenzen, kurze maximale Renderzeit), dann mit der 30-Bilder-Testdatei prüfen, ob EEVEE dort läuft;
  sonst die Szene für Cycles auslegen. Aufgabe in der App „Planung“.
- Blender-Video (`BLENDER_AUFTRAG.md`, Aufgabe #50): Anfang heller gemacht (29.10.2026, siehe Verlauf),
  wartet auf Tobias' Blick auf die neuen Probebilder. Dann finales Rendern über Nacht, lokal, aus der
  Arbeitskopie `.claude/worktrees/anfang-heller`:
  `caffeinate -i nice -n 19 zsh -c 'blender/render.sh 16x9 100 final && blender/render.sh 9x16 100 final'`
  (ca. 2 h, abbrechbar und fortsetzbar). → alte Videos nach `assets/alt/`, neue als `assets/hero-*.mp4`
  (je höchstens ca. 3 MB) und Standbilder als `poster-*.jpg` → auf der Seite prüfen → Tobias gibt frei → pushen.
